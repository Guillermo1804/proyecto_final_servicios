import os
import sys

# ensure service package imports work when run from the service dir
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from grpc_clients import get_alumno_by_id, validate_token


if __name__ == '__main__':
    print('Testing get_alumno_by_id(1)')
    try:
        resp = get_alumno_by_id(1)
        print('Response:', resp)
    except Exception as e:
        print('Error calling GetAlumnoById:', e)

    print('\nTesting validate_token("dummy")')
    try:
        resp = validate_token('dummy')
        print('Response:', resp)
    except Exception as e:
        print('Error calling ValidateToken:', e)
