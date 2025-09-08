from django.apps import AppConfig


class AdminAccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_account'

    def ready(self):
        import admin_account.signals  # 👈 ensures signals are registered
