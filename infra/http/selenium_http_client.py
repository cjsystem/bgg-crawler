from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumHttpClient:
    """SeleniumベースのHTTPクライアント（JavaScript実行対応）"""

    def __init__(self,
                 headless: bool = True,
                 timeout: int = 10,
                 user_agent: str = None,
                 save_html: bool = False,
                 output_dir: str = "output"):
        """
        Args:
            headless (bool): ヘッドレスモードで実行するか
            timeout (int): ページ読み込みタイムアウト秒数
            user_agent (str): User-Agentヘッダー
            save_html (bool): HTMLファイルを保存するか
            output_dir (str): HTML保存ディレクトリ
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.save_html = save_html
        self.output_dir = Path(output_dir)
        self.driver = None

        if self.save_html:
            self.output_dir.mkdir(exist_ok=True)

    def __enter__(self):
        self._setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def _setup_driver(self):
        """WebDriverの設定"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={self.user_agent}")

        # パフォーマンス向上のオプション
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=chrome_options)

        # WebDriverの検出を回避
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def get_html(self,
                 url: str,
                 wait_element: Dict[str, str] = None,
                 additional_wait: int = 0) -> Optional[str]:
        """
        URLからHTMLを取得

        Args:
            url (str): 取得するURL
            wait_element (Dict[str, str]): 待機する要素 {"by": "class_name", "value": "summary"}
            additional_wait (int): 要素待機後の追加待機時間（秒）

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """

        try:
            # 初期待機
            time.sleep(5)

            # ページにアクセス
            self.driver.get(url)

            # 指定された要素の読み込み完了を待つ
            if wait_element:
                by_type = getattr(By, wait_element.get("by", "CLASS_NAME").upper())
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((by_type, wait_element["value"]))
                )

            # 追加の待機時間
            if additional_wait > 0:
                time.sleep(additional_wait)  # ← ローカルインポートを削除

            html_content = self.driver.page_source

            # HTMLファイル保存（オプション）
            if self.save_html:
                self._save_html_file(html_content, url)

            return html_content

        except Exception as e:
            print(f"Error getting HTML from {url}: {str(e)}")
            return None

    def get_bgg_game_html(self, bgg_id: int) -> Optional[str]:
        """
        BGGゲームページのHTMLを取得（特化メソッド）

        Args:
            bgg_id (int): BGGのゲームID

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """
        url = f"https://boardgamegeek.com/boardgame/{bgg_id}"
        wait_element = {"by": "class_name", "value": "summary"}

        html_content = self.get_html(url, wait_element, additional_wait=2)

        if html_content and self.save_html:
            # BGG専用のファイル名で保存
            self._save_bgg_html_file(html_content, bgg_id)

        return html_content

    def _save_html_file(self, html_content: str, url: str) -> None:
        """HTMLファイルを保存（汎用）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # URLから安全なファイル名を作成
        safe_url = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "_")
        filename = self.output_dir / f"html_{safe_url}_{timestamp}.html"
        filename.write_text(html_content, encoding='utf-8')
        print(f"HTML content saved to {filename}")

    def _save_bgg_html_file(self, html_content: str, bgg_id: int) -> None:
        """BGG専用HTMLファイルを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"bgg_{bgg_id}_{timestamp}.html"
        filename.write_text(html_content, encoding='utf-8')
        print(f"BGG HTML content saved to {filename}")

    def execute_javascript(self, script: str) -> Any:
        """JavaScriptを実行"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            print(f"Error executing JavaScript: {str(e)}")
            return None

    def get_current_url(self) -> str:
        """現在のURLを取得"""
        return self.driver.current_url if self.driver else ""

    def get_title(self) -> str:
        """ページタイトルを取得"""
        return self.driver.title if self.driver else ""


class SeleniumHttpClientException(Exception):
    """SeleniumHttpClient例外"""
    pass