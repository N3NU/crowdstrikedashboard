from datetime import datetime
import pytz

def to_local_time(UTC):
    # Input UTC datetime string
    utc_datetime_str = UTC

    # Remove the fractional seconds and 'Z'
    utc_datetime_str = utc_datetime_str.split('.')[0] + 'Z'

    # Parse the string to a datetime object
    utc_datetime = datetime.strptime(utc_datetime_str, '%Y-%m-%dT%H:%M:%S%z')

    # Define the target timezone (Eastern Standard Time)
    est_timezone = pytz.timezone('US/Eastern')

    # Convert the UTC datetime to EST
    est_datetime = utc_datetime.astimezone(est_timezone)
    return est_datetime.strftime('%Y-%m-%d %H:%M:%S')


#USED IN THE FLATTEN_DICT FUNCTION
def flatten_value(value):
    if isinstance(value, dict):
        return ', '.join([f"{k}: {v}" for k, v in value.items()])
    elif isinstance(value, list):
        return ', '.join(map(str, value))
    return value

#REMOVE DICTIONARIES AND LIST VALUES FROM DICTIONARY
def flatten_dict(d):
    flattened = {}
    for k, v in d.items():
        if k == 'show_in_ui' and v == False:
            None
        else:
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, dict):
                        flattened.update(flatten_dict(v2))
                    elif isinstance(v2, list):
                        flattened[k2] = flatten_value(v2)
                    else:
                        flattened[k2] = flatten_value(v2)
            # flattened[k] = flatten_value(v)
            elif isinstance(v, list):
                for i in range(0, len(v)):
                    if isinstance(v[i], dict):
                        for k2, v2 in v[i].items():
                            if isinstance(v2, dict):
                                flattened.update(flatten_dict(v2))
                            elif isinstance(v2, list):
                                flattened[k2 + f'{i}'] = flatten_value(v2)
                            else:
                                flattened[k2 + f'{i}'] = flatten_value(v2)
                    else:
                        flattened[k + f'{i}'] = v[i]
                #flattened[k] = flatten_value(v)
            else:
                flattened[k] = v
            if k == 'created_timestamp':
                flattened[k] = to_local_time(v)
    return flattened

if __name__ == '__main__':
    None