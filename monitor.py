import time
from playwright.sync_api import sync_playwright

# --- 请根据您的需求修改以下变量 ---

# 1. 网站信息
LOGIN_URL = 'https://example.com/login'  # 登录页面的URL
TARGET_URL = 'https://example.com/target-page' # 您要监控的页面的URL

# 2. 登录凭据 (重要提示：直接在代码中写入密码不安全，建议使用环境变量等方式)
USERNAME = 'your_username'
PASSWORD = 'your_password'

# 3. 监控内容
# 您期望在页面上看到的特定文字或元素的选择器 (CSS Selector)
# 例如，如果想找一个 class="important-notice" 的元素，就写 '.important-notice'
# 如果只是想找一段文字，可以直接写文字内容
CONTENT_TO_FIND = '您要查找的特定文字'

# 4. 检查频率
# 每次检查之间的等待时间（单位：秒）
# 例如 10 * 60 就是10分钟
CHECK_INTERVAL_SECONDS = 10 * 60

# --- 脚本主逻辑 ---

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False 会显示浏览器界面，方便调试
        page = browser.new_page()

        # --- 步骤1: 登录 ---
        print("正在尝试登录...")
        page.goto(LOGIN_URL)
        
        # 以下选择器需要根据实际网站的HTML结构进行修改
        # 您可以使用浏览器的开发者工具 (F12) 来查找输入框和按钮的id或name
        page.fill('input[name="username"]', USERNAME) # 找到用户名字段并输入
        page.fill('input[name="password"]', PASSWORD) # 找到密码字段并输入
        page.click('button[type="submit"]') # 点击登录按钮
        
        # 等待登录成功后的页面跳转
        page.wait_for_url(lambda url: url != LOGIN_URL, timeout=60000)
        print("登录成功！")

        # --- 步骤2: 循环监控 ---
        print(f"开始监控页面: {TARGET_URL}")
        print(f"每隔 {CHECK_INTERVAL_SECONDS / 60} 分钟检查一次...")

        while True:
            try:
                print(f"[{time.ctime()}] 正在检查页面...")
                page.goto(TARGET_URL, wait_until='domcontentloaded')

                # 检查特定内容是否存在
                content = page.content()
                if CONTENT_TO_FIND in content:
                    print("\n!!! 目标内容已出现! !!!")
                    print(f"页面: {TARGET_URL}")
                    print(f"出现时间: {time.ctime()}")
                    
                    # 在这里您可以添加发送通知的代码，例如发送邮件或调用API
                    
                    break  # 找到内容，退出循环
                else:
                    print("目标内容尚未出现。")

                print(f"等待 {CHECK_INTERVAL_SECONDS / 60} 分钟后进行下一次检查...")
                time.sleep(CHECK_INTERVAL_SECONDS)

            except Exception as e:
                print(f"发生错误: {e}")
                print("将在1分钟后重试...")
                time.sleep(60)

        browser.close()

if __name__ == '__main__':
    main()
