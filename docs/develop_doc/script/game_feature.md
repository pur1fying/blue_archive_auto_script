# 图像识别

主要方法:
1. [模板匹配](#模板匹配)
    - 对应文件路径 : `"core/image.py"`
2. [比较像素值](#比较像素值)
    - 对应文件路径 : `"core/color.py"`
3. [OCR](/develop_doc/script/ocr)
4. TODO:: yolo目标检测

## 模板匹配
- **description**: 通常用于识别游戏中静态的图像, 例如一些**按钮**, **图标**
例:
1. 下图为游戏商店截图, 红色方框内的元素都是这个页面不变的元素, 当模板匹配函数认定这些元素存在时, 我们认为我们在商店界面
   - ![img](/assets/game_feature/static_feature_example.png)
2.  如图绿框中的元素, 会随着用户滑动屏幕而上下平移, 但是本体不会发生变化, 可以使用模板匹配判断是否出现, 出现坐标在哪
   - ![img](/assets/game_feature/static_feature_example2.png)

**note**: 
- 对于1. 模板图像的位置固定, 我们只需要根据模板图像采集区域, 截取截图中的对应区域, 然后进行匹配 (两张长宽相同的图像作比较)
    - **related functions**:
        1. [`compare_image`](#compare-image)
- 对于2. 由于模板图像在截图中的位置不固定, 我们需要在它可出现区域内进行模板匹配, 获取最高的匹配度, 从而判断是否出现
    - **related functions**:
        1. [`search_in_area`](#search-in-area)
        2. [`search_image_in_area`](#search-image-in-area)
        3. [`get_image_all_appear_position`](#get-image-all-appear-position)
      
有关滑动（swipe）
1. BAAS 大部分滑动都是默认会滑动到理想的位置，即没有做检测的，由于不同电脑性能不同，这会导致类似这种问题 #98
2. 滑动时我们希望:
    - 检测本次滑动导致 y 平移多少像素 （1. [普通商店](https://github.com/pur1fying/blue_archive_auto_script/blob/master/module/common_shop.py#L93) 2. [制造](https://github.com/pur1fying/blue_archive_auto_script/blob/master/module/common_shop.py#L93)
    - 滑动直至某一个图像特征出现，在这里 我们希望得知滑动后需要选择的预设队伍编号是否出现
3. 所以我在考虑能否归纳一个函数能满足这类需求，帮助BAAS避免不稳定的滑动 
## 比较像素值


## 函数列表
**note**: 请阅读源码
### `compare_image`

### `search_in_area` 

### `search_image_in_area`

### `get_image_all_appear_position`