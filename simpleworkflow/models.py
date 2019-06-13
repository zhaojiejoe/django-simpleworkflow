from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from django.contrib.auth.models import Group


class WorkFlow(models.Model):
    code = models.CharField(
        _("workflow code"), max_length=30)
    name = models.CharField(
        _("workflow name"), max_length=50)
    description = models.TextField(_("description"), blank=True, null=True)
    date_created = models.DateTimeField(_("date_created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("date_updated"), auto_now=True)

    def __str__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = _("workflow")
        verbose_name_plural = _("workflow")


class LogicType(object):
    logic_any = 1
    logic_all = 2


class WorkFlowNode(models.Model):
    LOGIC_TYPE = (
        (LogicType.logic_any, _("ANY")),
        (LogicType.logic_all, _("ALL")),
    )
    workflow = models.ForeignKey(WorkFlow)
    code = models.CharField(
        _("node code"), max_length=30)
    name = models.CharField(
        _("node name"), max_length=50)
    is_start = models.BooleanField(_("start node"), default=False)
    is_end = models.BooleanField(_("end node"), default=False)
    users = models.ManyToManyField(
        User, verbose_name=_("designated user"), blank=True)
    groups = models.ManyToManyField(
        Group, verbose_name=_("designated group"), blank=True)
    logic_type = models.IntegerField(
        _("logic type"), choices=LOGIC_TYPE, default=LogicType.logic_all)
    next_node = models.ForeignKey(
        'self', verbose_name=_("next node"), blank=True, null=True)
    date_created = models.DateTimeField(_("date_created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("date_updated"), auto_now=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.code:
            fmt = 'N%02d'
            self.code = fmt % (self.workflow.node_set.count()+1)
        super(WorkFlowNode, self).save(
            force_insert, force_update, using, update_fields)

    def __str__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = _("workflow_node")
        verbose_name_plural = _("workflow_node")


class WorkFlowInstanceType(object):
    new = 1
    in_progress = 2
    deny = 3
    terminated = 4
    completed = 99


class WorkFlowInstance(models.Model):
    WORKFLOW_STATUS = (
        (WorkFlowInstanceType.new, _("NEW")),
        (WorkFlowInstanceType.in_progress, _("IN PROGRESS")),
        (WorkFlowInstanceType.deny, _("DENY")),
        (WorkFlowInstanceType.terminated, _("TERMINATED")),
        (WorkFlowInstanceType.completed, _("COMPLETED"))
    )
    workflow = models.ForeignKey(WorkFlow)
    code = models.CharField(_("instance code"), blank=True,
                            null=True, max_length=20)
    name = models.CharField(_("instance name"), blank=True,
                            null=True, max_length=50)
    starter = models.ForeignKey(User, verbose_name=_("start user"))
    content_type = models.ForeignKey(ContentType,
                                     verbose_name=_("content_type"))
    object_id = models.PositiveIntegerField(_("object_id"))
    content_object = GenericForeignKey('content_type', 'object_id')
    workflow_status = models.IntegerField(
        _("workflow status"), choices=WORKFLOW_STATUS, default=WorkFlowInstanceType.new)
    is_new = models.BooleanField(_('newest_instance'), default=True)
    current_node = models.ForeignKey(WorkFlowNode, null=True)
    date_created = models.DateTimeField(
        _("date_created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("date_updated"), auto_now=True)

    def __str__(self):
        return "%s" % self.code

    class Meta:
        verbose_name = _("workflow_instance")
        verbose_name_plural = _("workflow_instance")


class WorkFlowProcessType(object):
    init = 0
    agree = 1
    deny = 2
    submit = 3
    terminated = 4


class WorkFlowProcess(models.Model):
    PROCESS_TYPE = (
        (WorkFlowProcessType.init, _("INIT")),
        (WorkFlowProcessType.agree, _("AGREE")),
        (WorkFlowProcessType.deny, _("DENY")),
        (WorkFlowProcessType.terminated, _("TERMINATED")),
        (WorkFlowProcessType.submit, _("SUBMIT")),
    )
    inst = models.ForeignKey(
        WorkFlowInstance, verbose_name=_("workflow instance"))
    node = models.ForeignKey(WorkFlowNode, verbose_name=_(
        "current node"), blank=True, null=True)
    user = models.ForeignKey(User, verbose_name=_("submitter"))
    todo = models.BooleanField(_("is todo"), default=False)
    pro_time = models.DateTimeField(_("process time"), null=True)
    pro_type = models.IntegerField(
        _("process type"), choices=PROCESS_TYPE, default=WorkFlowProcessType.init)
    note = models.TextField(
        _("note"), blank=True, null=True)
    date_created = models.DateTimeField(
         _("date_created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("date_updated"), auto_now=True)

    def __str__(self):
        return "process:%s-%s" % (self.user, self.node)

    class Meta:
        verbose_name = _("workflow_process")
        verbose_name_plural = _("workflow_process")
