import math
from worklocation.models import WorkLocation
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

def get_work_location_by_employee_and_date(employee, date=None):
    """
    Lấy WorkLocation theo employee và date.
    Nếu date là None thì lấy mặc định là hôm nay.
    Trả về instance WorkLocation hoặc None nếu không có.
    """
    if date is None:
        date = timezone.now().date()

    try:
        work_location = WorkLocation.objects.get(employee=employee, date=date)
        return work_location
    except ObjectDoesNotExist:
        return None
def haversine(lat1, lon1, lat2, lon2):
    """
    Tính khoảng cách giữa 2 điểm trên Trái Đất theo tọa độ latitude và longitude.
    Trả về khoảng cách đơn vị mét.
    """
    R = 6371e3  # Bán kính Trái Đất tính bằng mét

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # Khoảng cách tính bằng mét
    return distance
