import functools
import json
import datetime

from django.db import models


class Log(models.Model):
    message = models.TextField(verbose_name='Message', )
    type = models.IntegerField(verbose_name='Type', null=True)
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(verbose_name='Action', max_length=512, null=True)
    duration_ms = models.IntegerField(verbose_name='Duration(ms)', null=True)
    json = models.TextField(verbose_name='Json', null=True)
    # status: 0 for success, 1 for error, 2 for warning
    status = models.IntegerField(verbose_name='Status')

    class Meta:
        db_table = 'Log'
        ordering = ('-id',)
        verbose_name = 'Log'
        verbose_name_plural = verbose_name

    @classmethod
    def log_this(cls, track_type=0, save_param=False):
        """
        :param track_type: 0 for normal function
        :param save_param: save the function param
        :return:  decorator

        from Log import log_this
        # set the track_type(int), 1 for api selenium crawler, 2 for pyautogui crawler
        log_this = log_mail_processing(track_type)

        @log_this
        def f1():
            return status, original_return

        a = f1() # a == original_return, the status will get by log_this and exclude in function return
        """

        def decorator(f):
            """Decorator to log user actions"""

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                start_dttm = datetime.datetime.now()
                outs = f(*args, **kwargs)

                if isinstance(outs, tuple):
                    status = outs[0]
                    if len(outs) > 2:
                        value = outs[1:]
                    else:
                        value = outs[1]
                else:
                    status = outs
                    value = None

                # None means don't save anything
                if status is None:
                    return value

                if save_param:
                    status['parameters'] = {
                        'args': args,
                        'kwargs': kwargs
                    }

                cls.objects.create(
                    action=f.__name__,
                    type=track_type,
                    duration_ms=(datetime.datetime.now() - start_dttm).total_seconds() * 1000,
                    json=json.dumps(status),
                    status=status['status'],
                    message=status.get('message', '')
                )
                return value
            return wrapper
        return decorator
