from concurrent.futures import ThreadPoolExecutor

from DrissionPage import Chromium, ChromiumOptions
import base64
import time
import os

siteKey = '0x4AAAAAABA4JXCaw9E2Py-9'
siteUrl = 'https://testnet.megaeth.com/'
# 2. 读取本地 HTML 内容
with open('fakePage.html', 'r', encoding='utf-8') as f:
    fake_html = f.read().replace('<site-key>', siteKey)


def format_Headers(headers):
    _headers = []
    for header in headers:
        _headers.append({"name": header, "value": headers.get(header)})
    return _headers


def format_Body(body):
    base64_body = base64.b64encode(body).decode("utf-8")
    return base64_body


class SetRequestResponse:
    def __init__(self, browser: Chromium, urls: list) -> None:
        """

        :param page:
        :param urls: 字典数组[{
                            url:地址
                            response:替换成的内容
                            }]
        """
        self.browser = browser
        self.urls = urls
        self.start()

    def start(self):
        self.browser._run_cdp("Fetch.enable")
        self._set_callback()

    def _set_callback(self):
        self.browser._driver.set_callback("Fetch.requestPaused", self.response_change)

    def response_change(self, **kwargs):
        request_url = kwargs.get("request").get("url")
        headers = kwargs.get("request").get("headers")
        for url in self.urls:
            if url['url'] == request_url:
                self.browser._run_cdp(
                    "Fetch.fulfillRequest",
                    requestId=kwargs.get("requestId"),
                    body=format_Body(url['response'].encode()),
                    responseHeaders=format_Headers(headers),
                    responseCode=200
                )
            else:
                self.browser._run_cdp(
                    "Fetch.continueRequest",
                    requestId=kwargs.get("requestId")
                )


co = ChromiumOptions()
co.auto_port()

co.set_timeouts(base=1)

# change this to the path of the folder containing the extension
EXTENSION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "turnstilePatch"))
co.add_extension(EXTENSION_PATH)
co.headless()
co.set_user_agent(f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

browser = Chromium(co)

page = browser.get_tabs()[-1]

def getTurnstileToken():
    arr = [{
        'url': siteUrl,
        'response': fake_html
    }]
    SetRequestResponse(page, arr)
    page.get(siteUrl)
    page.run_js("try { turnstile.reset() } catch(e) { }")

    turnstileResponse = None

    for i in range(0, 15):
        try:
            turnstileResponse = page.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
            if turnstileResponse:
                return turnstileResponse

            challengeSolution = page.ele("@name=cf-turnstile-response")
            challengeWrapper = challengeSolution.parent()
            challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
            challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
            challengeButton = challengeIframeBody.ele("tag:input")
            challengeButton.click()
        except Exception as e:
            pass

    page.refresh()
    raise Exception("failed to solve turnstile")


while True:
    try:
        Turnstile = getTurnstileToken()
        print(Turnstile)
    except Exception as e:
        pass




