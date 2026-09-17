"""Vocabulary lookup utility for adding custom words."""

import json
import html
import logging
import re
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from utils.app_logger import get_app_logger


LOGGER = get_app_logger("english_helper.lookup")
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("lookup.log") for h in LOGGER.handlers):
    legacy_handler = logging.FileHandler("lookup.log", encoding="utf-8")
    legacy_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    LOGGER.addHandler(legacy_handler)


class VocabularyLookupService:
    """Fetches word metadata and Chinese translation from public APIs."""

    WIKTIONARY_API = "https://en.wiktionary.org/api/rest_v1/page/definition/{}"
    DICT_API = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"
    TRANS_API = "https://api.mymemory.translated.net/get?q={}&langpair=en|zh-TW"
    BACKUP_API = "https://api.datamuse.com/words?sp={}&md=d&max=1"
    PROVIDER_ORDER = ["wiktionary", "dictionaryapi", "datamuse"]

    def __init__(self):
        self.local_vocab = self._load_local_vocab()
        self.last_error_code = None
        self.last_error_message = ""
        self.provider_state = {
            "wiktionary": {"fail_count": 0, "cooldown_until": 0.0},
            "dictionaryapi": {"fail_count": 0, "cooldown_until": 0.0},
            "datamuse": {"fail_count": 0, "cooldown_until": 0.0},
        }

    def _load_local_vocab(self) -> Dict[str, Dict[str, str]]:
        vocab = {}
        for file_name, root_key in [
            ("vocabulary_core.json", "words"),
            ("vocabulary_custom.json", "custom_words"),
        ]:
            path = Path(file_name)
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for item in data.get(root_key, []):
                    english = str(item.get("english", "")).strip().lower()
                    if english:
                        vocab[english] = {
                            "chinese": self._clean_text(str(item.get("chinese", ""))),
                            "part_of_speech": self._clean_text(str(item.get("part_of_speech", ""))),
                        }
            except Exception as err:
                LOGGER.warning("Failed loading local vocab from %s: %s", file_name, err)
        return vocab

    def _lookup_backup(self, word: str) -> Dict[str, str]:
        backup = {"part_of_speech": "", "definition": ""}
        data = self._get_json(self.BACKUP_API.format(quote(word)), provider_name="datamuse")
        if not isinstance(data, list) or not data:
            return backup

        first = data[0]
        defs = first.get("defs", []) if isinstance(first, dict) else []
        if defs:
            # Datamuse defs format: "pos\tdefinition"
            head = str(defs[0])
            if "\t" in head:
                pos, definition = head.split("\t", 1)
                backup["part_of_speech"] = pos.strip()
                backup["definition"] = definition.strip()
            else:
                backup["definition"] = head.strip()

        return backup

    def _mark_provider_result(self, provider_name: str, success: bool, error_code=None):
        state = self.provider_state.get(provider_name)
        if not state:
            return

        if success:
            state["fail_count"] = 0
            state["cooldown_until"] = 0.0
            return

        state["fail_count"] += 1
        # 403 usually means blocked; use longer cooldown.
        cooldown_seconds = 600 if error_code == 403 else 180
        state["cooldown_until"] = time.time() + cooldown_seconds

    def _provider_available(self, provider_name: str) -> bool:
        state = self.provider_state.get(provider_name, {})
        return time.time() >= float(state.get("cooldown_until", 0.0))

    def health_check(self) -> Dict[str, Dict[str, str]]:
        """Return provider health summary and refresh cooldown states."""
        status = {}
        probe_word = "apple"

        endpoints = {
            "wiktionary": self.WIKTIONARY_API.format(quote(probe_word)),
            "dictionaryapi": self.DICT_API.format(quote(probe_word)),
            "datamuse": self.BACKUP_API.format(quote(probe_word)),
        }

        for provider_name, url in endpoints.items():
            data = self._get_json(url, timeout=5, provider_name=provider_name)
            ok = bool(data)
            status[provider_name] = {
                "ok": str(ok),
                "fail_count": str(self.provider_state[provider_name]["fail_count"]),
                "cooldown_until": str(int(self.provider_state[provider_name]["cooldown_until"])),
                "last_error": self.last_error_message,
            }

        LOGGER.info("Provider health check: %s", status)
        return status

    def _get_json(self, url: str, timeout: int = 6, provider_name: str = "") -> Optional[Dict]:
        self.last_error_code = None
        self.last_error_message = ""
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                if provider_name:
                    self._mark_provider_result(provider_name, True)
                return data
        except HTTPError as err:
            self.last_error_code = err.code
            self.last_error_message = str(err.reason)
            LOGGER.error("HTTPError when requesting %s: code=%s reason=%s", url, err.code, err.reason)
            if provider_name:
                self._mark_provider_result(provider_name, False, err.code)
            return None
        except URLError as err:
            self.last_error_message = str(getattr(err, "reason", err))
            LOGGER.error("URLError when requesting %s: reason=%s", url, getattr(err, "reason", err))
            if provider_name:
                self._mark_provider_result(provider_name, False)
            return None
        except TimeoutError:
            self.last_error_message = "timeout"
            LOGGER.error("Timeout when requesting %s", url)
            if provider_name:
                self._mark_provider_result(provider_name, False)
            return None
        except json.JSONDecodeError as err:
            self.last_error_message = "invalid_json"
            LOGGER.error("Invalid JSON from %s: %s", url, err)
            if provider_name:
                self._mark_provider_result(provider_name, False)
            return None
        except Exception as err:
            self.last_error_message = str(err)
            LOGGER.exception("Unexpected error when requesting %s: %s", url, err)
            if provider_name:
                self._mark_provider_result(provider_name, False)
            return None

    def _translate_to_chinese(self, text: str) -> str:
        if not text:
            return ""
        translated = self._get_json(self.TRANS_API.format(quote(text)))
        if not translated:
            return ""
        value = translated.get("responseData", {}).get("translatedText", "")
        return self._clean_text(value)

    def _clean_text(self, text: str) -> str:
        cleaned = html.unescape(text or "")
        cleaned = cleaned.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        cleaned = cleaned.replace("\u00a0", " ")
        cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _clean_example_text(self, text: str) -> str:
        cleaned = self._clean_text(text)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        return cleaned

    def _extract_from_wiktionary(self, word: str) -> Dict:
        data = self._get_json(self.WIKTIONARY_API.format(quote(word)), provider_name="wiktionary")
        if not isinstance(data, dict):
            return {}

        entries = data.get("en", [])
        if not entries:
            return {}

        part_of_speech = ""

        for entry in entries:
            if not part_of_speech:
                part_of_speech = str(entry.get("partOfSpeech", "")).strip().lower()

        return {
            "part_of_speech": part_of_speech,
            "source": "wiktionary",
        }

    def _extract_from_dictionaryapi(self, word: str) -> Dict:
        data = self._get_json(self.DICT_API.format(quote(word)), provider_name="dictionaryapi")
        if not isinstance(data, list) or not data:
            return {}

        entry = data[0]
        part_of_speech = ""
        meanings = entry.get("meanings", [])

        for meaning in meanings:
            if not part_of_speech:
                part_of_speech = str(meaning.get("partOfSpeech", "")).strip().lower()
            if part_of_speech:
                break

        return {
            "part_of_speech": part_of_speech,
            "source": "dictionaryapi",
        }

    def _extract_from_provider(self, provider_name: str, word: str) -> Tuple[Dict, Optional[int], str]:
        if provider_name == "wiktionary":
            result = self._extract_from_wiktionary(word)
        elif provider_name == "dictionaryapi":
            result = self._extract_from_dictionaryapi(word)
        else:
            backup = self._lookup_backup(word)
            result = {
                "part_of_speech": backup.get("part_of_speech", ""),
                "source": "datamuse",
            }

        return result, self.last_error_code, self.last_error_message

    def lookup_word(self, word: str) -> Dict:
        clean_word = (word or "").strip().lower()
        if not clean_word:
            return {"success": False, "error": "請先輸入英文單字"}

        if not re.fullmatch(r"[a-zA-Z][a-zA-Z\-']*", clean_word):
            return {"success": False, "error": "請輸入有效英文單字（僅英文字母、-、'）"}

        LOGGER.info("Lookup start: %s", clean_word)

        part_of_speech = ""
        provider_used = ""
        provider_errors = []

        candidates = [p for p in self.PROVIDER_ORDER if self._provider_available(p)]
        if not candidates:
            # all providers are in cooldown, still try them in order
            candidates = list(self.PROVIDER_ORDER)

        for provider_name in candidates:
            extracted, err_code, err_msg = self._extract_from_provider(provider_name, clean_word)
            has_value = bool(extracted.get("part_of_speech"))
            if has_value:
                part_of_speech = extracted.get("part_of_speech", "")
                provider_used = extracted.get("source", provider_name)
                LOGGER.info("Dictionary provider selected provider=%s word=%s", provider_used, clean_word)
                break

            provider_errors.append((provider_name, err_code, err_msg))

        # Prefer translating the word itself; fallback to definition text if needed.
        chinese = self._translate_to_chinese(clean_word)
        if not chinese:
            chinese = self._translate_to_chinese(clean_word.replace("-", " "))

        if not provider_used and not chinese:
            return {
                "success": False,
                "error": "查詢失敗：字典與翻譯服務都未回應，請稍後再試",
            }

        # Fallback 1: local vocabulary files
        local = self.local_vocab.get(clean_word, {})
        if local:
            if not chinese:
                chinese = local.get("chinese", "")
            if not part_of_speech:
                part_of_speech = local.get("part_of_speech", "")

        # Fallback 2: backup dictionary source
        if not part_of_speech:
            backup = self._lookup_backup(clean_word)
            part_of_speech = backup.get("part_of_speech", "")

        warning = ""
        if provider_used and provider_used != "wiktionary":
            warning = f"主字典服務暫時不可用，已自動切換至 {provider_used}"
        elif not provider_used:
            warning = "字典服務暫時不可用，僅提供翻譯與本地資料"

        if provider_errors:
            LOGGER.warning("Provider attempts failed: %s", provider_errors)

        result = {
            "success": True,
            "english": clean_word,
            "chinese": self._clean_text(chinese),
            "part_of_speech": self._clean_text(part_of_speech),
            "provider": provider_used or "translation_only",
        }
        if warning:
            result["warning"] = warning

        LOGGER.info(
            "Lookup done: %s (dict=%s, has_chinese=%s)",
            clean_word,
            bool(provider_used),
            bool(chinese),
        )
        return result
