from aqt import browser, gui_hooks, qt


def on_browser_will_show_context_menu(browser: browser.Browser, menu: qt.QMenu):
    from . import edge_tts_gen

    menu.addSeparator()
    menu.addAction("Generate edge-tts Audio", lambda: edge_tts_gen.onEdgeTTSOptionSelected(browser))


def on_browser_menus_did_init(browser: browser.Browser):
    from . import edge_tts_gen

    # Add to the Edit menu for easier access
    action = qt.QAction("Generate edge-tts Audio", browser)
    action.setShortcut(qt.QKeySequence("Ctrl+Shift+E"))
    action.triggered.connect(lambda: edge_tts_gen.onEdgeTTSOptionSelected(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(action)

    # Add "Generate Batch Audio" menu to the menu bar for easier access
    batch_menu = qt.QMenu("Generate Batch Audio", browser)
    batch_action = batch_menu.addAction("Configure and Generate...")
    batch_action.setShortcut(qt.QKeySequence("Ctrl+Shift+G"))
    batch_action.triggered.connect(lambda: edge_tts_gen.onEdgeTTSOptionSelected(browser))
    browser.form.menubar.addMenu(batch_menu)


gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)
gui_hooks.browser_menus_did_init.append(on_browser_menus_did_init)
