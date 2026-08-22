from gui.components.expand.shop_panel import ShopPanel, estimate_arena_daily


class Layout(ShopPanel):
    def __init__(self, parent=None, config=None):
        price_list = []
        try:
            price_list = config.static_config.tactical_challenge_shop_price_list[
                config.server_mode
            ]
        except Exception:
            try:
                live = getattr(config, "live", config)
                price_list = live.static_config.tactical_challenge_shop_price_list[
                    getattr(live, "server_mode", "CN")
                ]
            except Exception:
                price_list = []
        super().__init__(
            parent=parent,
            config=config,
            goods_key="TacticalChallengeShopList",
            refresh_key="TacticalChallengeShopRefreshTime",
            price_list=price_list,
            currency_icon="gui/assets/icons/item_icon_arenacoin.webp",
            currency_unit_label="单位：竞技币",
            refresh_max=3,
            estimate_fn=estimate_arena_daily,
        )
        try:
            self.unit_label.setText(self.tr("单位：竞技币"))
            self.refresh_label.setText(self.tr("购买刷新次数"))
            self.guide_label.setText(self.tr("请勾选购买物品"))
        except Exception:
            pass
