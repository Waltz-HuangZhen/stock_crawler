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


class FundType(models.Model):
    name = models.CharField(max_length=20)
    short_name = models.CharField(max_length=20)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'FundType'
        ordering = ('id',)
        verbose_name = 'FundType'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name + '-' + self.short_name


class FundCode(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    pinyin_name = models.CharField(max_length=200)
    fund_type = models.CharField(max_length=20)
    # models.ForeignKey(FundType, related_name='fund_type', on_delete=models.CASCADE)
    is_removed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'FundCode'
        ordering = ('code',)
        verbose_name = 'FundCode'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code + ': ' + self.name


class FundCodeDayWorth(models.Model):
    fund_code = models.ForeignKey(FundCode, related_name='fund_code', on_delete=models.CASCADE)
    date = models.DateField(null=False)
    nav = models.FloatField(null=True)
    accnav = models.FloatField(null=True)
    growth_rate = models.FloatField(verbose_name='Growth Rate(%)', null=True)
    seven_day_annual_yield = models.FloatField(verbose_name='7-day Annual Yield(%)', null=True)
    ten_thousands_annual = models.FloatField(verbose_name='10,000 Annual', null=True)
    purchased = models.CharField(max_length=20, null=True)
    redemption = models.CharField(max_length=20, null=True)
    dividend = models.CharField(max_length=50, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'FundCodeDayWorth'
        ordering = ('-date', 'fund_code__code')
        verbose_name = 'FundCodeDayWorth'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{:.4f}'.format(self.nav) if self.nav else '0.0'
