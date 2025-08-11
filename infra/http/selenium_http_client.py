# python
from typing import Optional, Dict, Any, Tuple, Iterable
from pathlib import Path
from datetime import datetime
import time
import random
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumHttpClient:
    """SeleniumベースのHTTPクライアント（JavaScript実行対応）
    - robots.txt の Crawl-delay: 5 を尊重（最低待機＋ジッター）
    - 失敗時の指数バックオフ付きリトライ
    - リソース負荷軽減（画像/フォント/プラグインなどのブロックをオプション化）
    """

    def __init__(self,
                 headless: bool = True,
                 timeout: int = 10,
                 user_agent: str = None,
                 save_html: bool = False,
                 output_dir: str = "output",
                 # 追加: ポライトネス/スロットリング
                 min_delay_seconds: float = 5.0,
                 jitter_range: Tuple[float, float] = (0.0, 3.0),
                 max_retries: int = 2,
                 backoff_base_seconds: float = 10.0,
                 backoff_cap_seconds: float = 120.0,
                 # 追加: リソースブロック
                 block_images: bool = True,
                 block_fonts: bool = True,
                 block_media: bool = True,
                 # 追加: 簡易的なDisallowパターンチェック（必要に応じて設定）
                 disallow_patterns: Optional[Iterable[str]] = None):
        """
        Args:
            headless: ヘッドレスモードで実行するか
            timeout: ページ読み込みタイムアウト秒数
            user_agent: User-Agentヘッダー
            save_html: HTMLファイルを保存するか
            output_dir: HTML保存ディレクトリ
            min_delay_seconds: 連続アクセスの最小待機秒数（Crawl-delay対応）
            jitter_range: 追加ジッターの範囲（秒）
            max_retries: 失敗時の最大リトライ回数
            backoff_base_seconds: バックオフの初期待機秒
            backoff_cap_seconds: バックオフ待機の上限秒
            block_images: 画像をブロックして負荷軽減
            block_fonts: フォントをブロックして負荷軽減
            block_media: メディア（動画/音声など）をブロックして負荷軽減
            disallow_patterns: アクセス前にURLを拒否するためのパターン文字列集（正規表現）
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.save_html = save_html
        self.output_dir = Path(output_dir)
        self.driver = None

        # Politeness settings
        self.min_delay_seconds = float(min_delay_seconds)
        self.jitter_range = jitter_range
        self.max_retries = int(max_retries)
        self.backoff_base_seconds = float(backoff_base_seconds)
        self.backoff_cap_seconds = float(backoff_cap_seconds)
        self._last_request_started_at: Optional[float] = None

        # Resource blocking
        self.block_images = block_images
        self.block_fonts = block_fonts
        self.block_media = block_media

        # Disallow rules (optional)
        self._disallow_regexes = [re.compile(p) for p in (disallow_patterns or [])]

        if self.save_html:
            self.output_dir.mkdir(exist_ok=True)

    def __enter__(self):
        self._setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def _setup_driver(self):
        """WebDriverの設定"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={self.user_agent}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--safebrowsing-disable-auto-update")

        # リソース軽量化（画像/フォント/メディアを必要に応じてブロック）
        prefs = {}
        if self.block_images:
            # 画像無効化
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            prefs["profile.managed_default_content_settings.images"] = 2
        if self.block_fonts:
            prefs["profile.managed_default_content_settings.fonts"] = 2
        if self.block_media:
            prefs["profile.managed_default_content_settings.plugins"] = 2
            prefs["profile.managed_default_content_settings.sound"] = 2
        if prefs:
            chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.timeout)

        # WebDriverの検出を回避
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            # 一部環境では失敗しても致命的ではない
            pass

    def _apply_polite_delay(self):
        """前回リクエストからの経過時間に基づく待機（Crawl-delay + ジッター）"""
        base = self.min_delay_seconds
        jitter = random.uniform(self.jitter_range[0], self.jitter_range[1]) if self.jitter_range else 0.0
        required = max(0.0, base + jitter)

        now = time.monotonic()
        if self._last_request_started_at is None:
            # 初回は規定の待機
            if required > 0:
                time.sleep(required)
            return

        elapsed = now - self._last_request_started_at
        remain = required - elapsed
        if remain > 0:
            time.sleep(remain)

    def _backoff_sleep(self, attempt: int):
        """指数バックオフ待機"""
        wait = min(self.backoff_cap_seconds, self.backoff_base_seconds * (2 ** max(0, attempt - 1)))
        if wait > 0:
            time.sleep(wait)

    def _is_disallowed(self, url: str) -> bool:
        """簡易的なDisallow判定（必要に応じて追加パターンを設定）"""
        for rx in self._disallow_regexes:
            if rx.search(url):
                return True
        return False

    def get_html(self,
                 url: str,
                 wait_element: Dict[str, str] = None,
                 additional_wait: int = 0) -> Optional[str]:
        """
        URLからHTMLを取得（ポライトネスとバックオフ込み）

        Args:
            url: 取得するURL
            wait_element: 待機する要素 {"by": "class_name"|"css_selector"|..., "value": "..."}
            additional_wait: 要素待機後の追加待機時間（秒）

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """
        # Disallowチェック（必要時のみ機能）
        if self._is_disallowed(url):
            raise SeleniumHttpClientException(f"URL is disallowed by local rule: {url}")

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 2):  # 例: max_retries=2 → 試行 3 回
            try:
                # ポライトネス（Crawl-delay + ジッター）
                self._apply_polite_delay()

                # リクエスト開始時刻を記録（次回の間隔確保）
                self._last_request_started_at = time.monotonic()

                # ページアクセス
                self.driver.get(url)

                # 指定要素の読み込み待機
                if wait_element:
                    by_key = (wait_element.get("by") or "CLASS_NAME").upper()
                    by_type = getattr(By, by_key, None)
                    if by_type is None:
                        raise SeleniumHttpClientException(f"Unsupported 'by' in wait_element: {by_key}")
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((by_type, wait_element["value"]))
                    )

                # 追加待機（描画安定化）
                if additional_wait and additional_wait > 0:
                    time.sleep(additional_wait)

                html_content = self.driver.page_source or ""
                if html_content.strip():
                    if self.save_html:
                        self._save_html_file(html_content, url)
                    return html_content

                # 空HTMLの場合は失敗扱い
                last_error = SeleniumHttpClientException("Empty page source")
                raise last_error

            except (TimeoutException, WebDriverException, SeleniumHttpClientException) as e:
                last_error = e
                if attempt <= self.max_retries:
                    self._backoff_sleep(attempt)
                    continue
                # リトライしきったらエラーとして終了
                break
            except Exception as e:
                last_error = e
                # 予期せぬ例外も同様にバックオフ＆リトライ
                if attempt <= self.max_retries:
                    self._backoff_sleep(attempt)
                    continue
                break

        # ここまで来たら失敗
        print(f"Error getting HTML from {url}: {last_error}")
        return None

    def get_bgg_game_html(self, bgg_id: int) -> Optional[str]:
        """BGGゲームページのHTMLを取得（特化メソッド）"""
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