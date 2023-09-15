import module


def func_select(func_name):
    module.__dict__[func_name].implement('implement')


func_select('collect_shop_power')
