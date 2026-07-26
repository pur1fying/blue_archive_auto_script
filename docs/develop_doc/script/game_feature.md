# 图像识别

主要方法:
1. [模板匹配](#模板匹配)
    - 对应文件路径 : `"core/image.py"`
2. [比较像素值](#比较像素值)
    - 对应文件路径 : `"core/color.py"`
3. [OCR](/develop_doc/script/ocr)
4. TODO:: yolo目标检测

## 模板匹配
- **description**: 在`BAAS`中, 我们通常使用模板匹配识别游戏中静态的图像, 例如一些**按钮**, **图标**, 
对于此类目标, 模板匹配能够在 1ms 内完成定位，且无需GPU资源，远快于深度学习模型。因此，在这种场景下，请使用模板匹配。
- **related docs**: 阅读以下例子可以帮助你理解模板匹配的使用场景和方法
    1. [OpenCV官方文档模板匹配例子](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html)
    2. [cv2.matchTemplate函数原型](https://docs.opencv.org/4.x/df/dfb/group__imgproc__object.html#ga586ebfb0a7fb604b35a23d85391329be)
- **pros**:
    1. 计算效率高：基于滑动窗口与相关系数计算，在CPU上即可实现毫秒级响应，满足实时性要求。
    2. 静态图像识别精确度高：
- **cons**: 
    1. 对缩放与旋转敏感：模板与待搜索图像的尺寸、方向必须严格一致，缩放或旋转将导致匹配失败。
    2. 对光照与噪声敏感：光照变化或噪声会显著降低匹配置信度。
    
`BAAS`中实际应用场景:
- 场景1 : `BAAS`如何判别是否到达商店界面
   - 下图为游戏商店截图, 红色方框内的元素都是这个页面**固定不变**的元素, 当模板匹配函数认定这些元素存在时, 程序认定抵达商店界面
   - ![img](/assets/game_feature/static_feature_example.png)
   - **note**: 对于这种场景, 我们采集固定的模板图像,并记录采集区域, 在识别时, 将截图中的对应区域与模板图像进行匹配, 
高于预设阈值时认为匹配成功, 程序也就知道了目前在商店界面
   - **related functions**:
       1. [`compare_image`](#compare-image)

- 场景2 : `BAAS` 如何切换到某个具体商店页面
  - 如图绿框中的商店名称, 会随着用户滑动左侧栏而上下平移, 但是图标本体并不会发生变化, 可以使用模板匹配判断目标商店图标是否出现, 出现坐标在哪
  - ![img](/assets/game_feature/static_feature_example2.png)
  - **note**: 由于模板图像在截图中的位置不固定, 我们需要在它可出现区域内进行模板匹配, 获取最高的匹配度, 从而判断是否出现
  - **related functions**:
      1. [`search_in_area`](#search-in-area)
      2. [`search_image_in_area`](#search-image-in-area)
      3. [`get_image_all_appear_position`](#get-image-all-appear-position)
      
有关滑动（swipe）
1. BAAS 大部分滑动都是默认会滑动到理想的位置, 即没有做检测的, 由于不同用户电脑性能不同, 这会导致滑动不到位的问题 [#98](https://github.com/pur1fying/blue_archive_auto_script/issues/98)
2. 滑动时我们希望:
    - 检测本次滑动导致 y 平移多少像素 
        1. 普通商店中, 我们在检测商品时需要下滑商品界面 [(相关代码)](https://github.com/pur1fying/blue_archive_auto_script/blob/master/module/shop/common_shop.py#L78) 
           - ![img](/assets/game_feature/swipe_example_common_shop.png)
        2. 制造中, 我们在选择制造投入物资时需要下滑物资界面 [(相关代码)](https://github.com/pur1fying/blue_archive_auto_script/blob/master/module/create.py#L807)
           - ![img](/assets/game_feature/swipe_example_create.png)
    - 滑动直至某一个图像特征出现
        1. 在使用预设配队时, 我们希望得知滑动后需要选择的预设队伍编号是否出现
            - ![img](/assets/game_feature/swipe_example_preset.png)
        2. 在活动图自动推图时, 我们希望知道滑动后目标关卡ID是否出现
            - ![img](/assets/game_feature/swipe_example_activity.png)
        - **note**: 对于这种场景, **BAAS**提供了[`swipe_search_target_str`](#swipe-search-target-str)函数, 


## 比较像素值


## 相关函数列表
**note**: 请阅读源码`"core/image.py"`
### `compare_image`
**description** : 将截图中的某个区域与目标图像进行模板匹配, 返回匹配度

### `search_in_area` 
**description** : 在截图的某个区域内搜索模板图像, 返回匹配度最高的坐标位置和匹配度

### `search_image_in_area`
**description** : 在截图的某个区域内搜索目标图像, 返回匹配度最高的坐标位置和匹配度
**note** : 与[`search_in_area`](#search-in-area)不同的是, 本函数需要在运行时截图并提供模板图像, 而前者从预设的模板寻找图像

### `get_image_all_appear_position`
**description** : 在截图的某个区域内搜索目标图像, 返回所有匹配度高于阈值的坐标位置

### `swipe_search_target_str`
**description** : 滑动搜索目标字符串, 直到找到, 返回目标字符串坐标