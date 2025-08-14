from django.apps import AppConfig


class UserappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'userapp'
    def ready(self):
        # Импортируем сигналы только после загрузки приложения
        import userapp.signals # these rows are important because we create specail file and here we activate signals