from __future__ import annotations


class SweetieBotAccessoriesPlugin:
    name = 'sweetiebot_accessories'

    def describe(self) -> dict:
        return {
            'name': self.name,
            'category': 'accessories',
            'provides': [
                'capability discovery',
                'cerberus onboard audio adapter metadata',
            ],
        }
