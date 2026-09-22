"""DCC bootstrap safety boundary."""
import logging
log = logging.getLogger("gameart.bootstrap")

def safe_bootstrap(start_callback):
    try:
        return start_callback()
    except Exception:
        log.exception("GameArt Toolkit failed; host DCC startup continues.")
        return None
