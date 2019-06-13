from itertools import chain
import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from simpleworkflow.models import (WorkFlow, WorkFlowNode,
                                   WorkFlowInstance, WorkFlowProcess)
from simpleworkflow.models import LogicType, WorkFlowProcessType, WorkFlowInstanceType


class WorkFlowService(object):

    @staticmethod
    def gain_workflow(code, name=None):
        workflow, _ = WorkFlow.objects.get_or_create(
            code=code, defaults={'name': name})
        return workflow

    @staticmethod
    def create_node(workflow, code, name, is_start, is_end, logic_type, users=None,
                    groups=None, previous_node=None):
        next_node = WorkFlowNode.objects.create(workflow=workflow,
                                                code=code, name=name,
                                                is_start=is_start, is_end=is_end, logic_type=logic_type)
        if previous_node is not None:
            previous_node.next_node = next_node
            previous_node.save()
        if users:
            next_node.users.add(*users)
        if groups:
            next_node.groups.add(*groups)
        return next_node

    @staticmethod
    def get_start_node(workflow):
        return WorkFlowNode.objects.filter(workflow=workflow, is_start=True).first()

    @staticmethod
    def start_workflow_instance(workflow, content_object, starter, code=None, name=None):
        WorkFlowInstance.objects.filter(is_new=True).update(is_new=False)
        workflowinstance = WorkFlowInstance.objects.filter(is_new=True).first()
        if workflowinstance is not None:
                WorkFlowService.handle_terminated_instance(workflowinstance)
        content_type = ContentType.objects.get_for_model(content_object)
        start_node = WorkFlowService.get_start_node(workflow)
        if start_node is None:
            return None
        workflowinstance = WorkFlowInstance.objects.create(
            workflow=workflow, current_node=start_node, starter=starter, object_id=content_object.id,
            content_type=content_type, code=code, name=name)
        return workflowinstance

    @staticmethod
    def create_workflow_process(workflowinstance, node, todo=False, users=None):
        if users is None:
            user_ids = node.users.values_list("pk", flat=True)
            group_user_ids = [group.user_set.values_list(
                "pk", flat=True) for group in node.groups.all()]
            users = User.objects.filter(
                pk__in=set(list(user_ids) + list(chain(*group_user_ids))))
        WorkFlowProcess.objects.bulk_create(
            [WorkFlowProcess(inst=workflowinstance, node=node,
                             todo=todo, user=user) for user in users])

    @staticmethod
    def handle_deny_instance(inst):
        WorkFlowProcess.objects.filter(inst=inst, pro_type=WorkFlowProcessType.init
                                       ).update(pro_type=WorkFlowProcessType.submit, todo=False)
        inst.workflow_status = WorkFlowInstanceType.deny
        inst.save()

    @staticmethod
    def handle_terminated_instance(inst):
        WorkFlowProcess.objects.filter(inst=inst, pro_type=WorkFlowProcessType.init
                                       ).update(pro_type=WorkFlowProcessType.terminated, todo=False)
        inst.workflow_status = WorkFlowInstanceType.terminated
        inst.save()

    @staticmethod
    def handle_agree_instance(inst):
        merge_to_next = False
        if inst.current_node.logic_type == LogicType.logic_any:
            WorkFlowProcess.objects.filter(inst=inst, pro_type=WorkFlowProcessType.init,
                                           node=inst.current_node
                                           ).update(pro_type=WorkFlowProcessType.submit, todo=False)
            merge_to_next = True
        else:
            if not WorkFlowProcess.objects.filter(inst=inst,
                                                  pro_type=WorkFlowProcessType.init,
                                                  node=inst.current_node).count():
                merge_to_next = True
        inst.workflow_status = WorkFlowInstanceType.in_progress
        if merge_to_next:
            next_node = inst.current_node.next_node
            if inst.current_node.next_node is None:
                inst.workflow_status = WorkFlowInstanceType.completed
            else:
                inst.current_node = next_node
                WorkFlowProcess.objects.filter(inst=inst,
                                               pro_type=WorkFlowProcessType.init, node=next_node
                                               ).update(todo=True)
        inst.save()

    @staticmethod
    def handle_workflow_process(workflowprocess, pro_type, note=None):
        workflowprocess.pro_time = datetime.datetime.now()
        workflowprocess.pro_type = pro_type
        workflowprocess.note = note
        workflowprocess.todo = False
        workflowprocess.save()
        if pro_type == WorkFlowProcessType.agree:
            WorkFlowService.handle_agree_instance(workflowprocess.inst)
        elif pro_type == WorkFlowProcessType.deny:
            WorkFlowService.handle_deny_instance(workflowprocess.inst)
