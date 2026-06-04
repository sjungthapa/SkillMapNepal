from django.apps import AppConfig
import warnings


class ScraperConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scraper"

    def ready(self):
        """Check Playwright installation on startup"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # Just check if playwright is accessible
                pass
        except ImportError:
            warnings.warn(
                "Playwright is not installed. "
                "Job scraping will fail. "
                "Run: pip install playwright && playwright install chromium",
                RuntimeWarning
            )
        except Exception:
            warnings.warn(
                "Playwright browsers not installed. "
                "Job scraping will fail. "
                "Run: playwright install chromium",
                RuntimeWarning
            )
