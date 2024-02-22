def get_context_thread(context, parent=None):
    if parent is None:
        parent = context.parent()
    for component in parent.children():
        if type(component).__name__ == 'HomeFragment' and context.config['name'] == component.config.get('name'):
            return component.get_main_thread()
    return get_context_thread(parent.parent())


