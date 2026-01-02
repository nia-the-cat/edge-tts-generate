from aqt import browser, gui_hooks, qt


def on_browser_will_show_context_menu(browser: browser.Browser, menu: qt.QMenu):
    from . import edge_tts_gen

    menu.addSeparator()
    menu.addAction(
        "Generate edge-tts Audio", lambda: edge_tts_gen.onEdgeTTSOptionSelected(browser)
    )


gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)
