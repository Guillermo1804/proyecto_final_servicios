import os
import sys

# ensure service package imports work when run from the service dir
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from grpc_clients import get_alumno_by_id


if __name__ == '__main__':
    print('Testing get_alumno_by_id(1) against ms-alumnos')
    try:
        resp = get_alumno_by_id(1)
        print('Response:', resp)
    except Exception as e:
        print('Error:', e)
