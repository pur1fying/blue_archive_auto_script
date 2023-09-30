# import module
#
#
# def func_select(func_name):
#     module.__dict__[func_name].implement('implement')
#
#
# func_select('collect_shop_power')


with open('requirements.txt', 'r') as f, open('requirements1.txt', 'w') as f1:
    for line in f.readlines():
        if "@" not in line and line != "\n":
            f1.write(line)
