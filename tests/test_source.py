from ipcodex.source import preprocess_text


def test_preprocess_preserves_line_numbers_and_indentation() -> None:
    document = preprocess_text(
        "sysname Leaf01\n#\ninterface 100GE1/0/1\n description TO-SPINE\n",
        source_name="leaf.cfg",
    )

    assert document.source_name == "leaf.cfg"
    assert [line.line_number for line in document.lines] == [1, 2, 3, 4]
    assert document.lines[3].raw_text == " description TO-SPINE"
    assert document.lines[3].normalized_text == " description TO-SPINE"
    assert document.lines[3].indentation == 1


def test_preprocess_removes_paging_artifacts_without_losing_source() -> None:
    document = preprocess_text(
        "interface 100GE1/0/1---- More ----\n description TEST\x1b[42D\n",
        source_name="leaf.cfg",
    )

    assert document.lines[0].raw_text.endswith("---- More ----")
    assert document.lines[0].normalized_text == "interface 100GE1/0/1"
    assert document.lines[1].normalized_text == " description TEST"


def test_blank_lines_are_retained_but_marked() -> None:
    document = preprocess_text("sysname Leaf01\n\n#\n", source_name="leaf.cfg")

    assert len(document.lines) == 3
    assert document.lines[1].is_blank is True
