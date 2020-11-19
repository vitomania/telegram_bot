import datetime as dt
from apscheduler.schedulers.blocking import BlockingScheduler


# Main cronjob function..
def cronjob():
    """
    Main cron job.
    The main cronjob to be run continuously.
    """
    print("Cron job is running")
    print("Tick! The time is: %s" % dt.datetime.now())


# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(cronjob, "interval", hours=1)

scheduler.start()
