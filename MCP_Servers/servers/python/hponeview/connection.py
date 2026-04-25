from hpOneView.oneview_client import OneViewClient
from config import ONEVIEW_CONFIG

def get_ov_client():
    return OneViewClient(ONEVIEW_CONFIG)
