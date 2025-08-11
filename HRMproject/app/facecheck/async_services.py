from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
@database_sync_to_async
def get_employee(self, user):
    try:
        return user.employee  # Truy cập quan hệ ngược
    except ObjectDoesNotExist:
        return None
    except AttributeError:
        return None