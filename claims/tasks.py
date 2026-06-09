from celery import shared_task
from .utils import process_df
import pandas as pd

@shared_task(bind=True)
def process_claims(excel_file,filetype,im_path):
    df = pd.read_excel(
        excel_file
    )
    im_df = pd.read_excel(im_path)
    process_df(df,filetype,im_df)
