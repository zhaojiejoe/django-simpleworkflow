from __future__ import unicode_literals

from model_mommy import mommy

from django.test import TestCase
from django.contrib.auth.models import User, Group

from simpleworkflow.models import (WorkFlow, WorkFlowNode,
                                   WorkFlowInstance, WorkFlowProcess)
from simpleworkflow.models import LogicType, WorkFlowProcessType, WorkFlowInstanceType, WorkFlowProcessType
from simpleworkflow.services import WorkFlowService


class WorkFlowServiceCreateTest(TestCase):
    def setUp(self):
        self.user1 = mommy.make(User)
        self.user2 = mommy.make(User)
        self.user3 = mommy.make(User)
        self.user4 = mommy.make(User)
        self.group1 = mommy.make(Group)
        self.group1.user_set.add(self.user1, self.user3)
        self.group2 = mommy.make(Group)
        self.group2.user_set.add(self.user1, self.user4)
        self.workflow = mommy.make(WorkFlow)

    def test_gain_workflow(self):
        code = "codedemo"
        name = "namedemo"
        workflow = WorkFlowService.gain_workflow(code, name)
        self.assertTrue(workflow.code == code, msg="create workflow code failed")
        self.assertTrue(workflow.name == name, msg="create workflow name failed")
        workflow = WorkFlowService.gain_workflow(code, name)
        self.assertTrue(workflow.code == code, msg="get workflow code failed")
        self.assertTrue(workflow.name == name, msg="get workflow name failed")
        print("===test_gain_workflow_ok===")

    def test_create_node(self):
        workflow = self.workflow
        code, name, is_start, is_end, logic_type = "demo1", "demo1", True, False, LogicType.logic_all
        users, groups, previous_node = [self.user1, self.user2], None, None
        node1 = WorkFlowService.create_node(workflow, code, name, is_start, is_end, logic_type, users,
                    groups, previous_node)
        self.assertTrue(node1.code == code, msg="create workflow node failed")
        self.assertTrue(node1.name == name, msg="create workflow name failed")
        self.assertTrue(node1.is_start == is_start, msg="create workflow is_start failed")
        self.assertTrue(node1.is_end == is_end, msg="create workflow is_end failed")
        self.assertTrue(node1.logic_type == LogicType.logic_all, msg="create workflow logic_type failed")
        self.assertIn(self.user1, node1.users.all(), msg="create workflow user1 failed")
        self.assertIn(self.user2, node1.users.all(), msg="create workflow user2 failed")
        code, name, is_start, is_end, logic_type = "demo2", "demo2", False, False, LogicType.logic_any
        users, groups, previous_node = None, None, node1
        node2 = WorkFlowService.create_node(workflow, code, name, is_start, is_end, logic_type, users,
                    groups, previous_node)
        self.assertTrue(node1.next_node == node2, msg="create workflow node2 failed")
        code, name, is_start, is_end, logic_type = "demo3", "demo3", False, True, LogicType.logic_all
        users, groups, previous_node = None, [self.group1, self.group2], node2
        node3 = WorkFlowService.create_node(workflow, code, name, is_start, is_end, logic_type, users,
                    groups, previous_node)
        self.assertIn(self.group1, node3.groups.all(), msg="create workflow group1 failed")
        self.assertIn(self.group2, node3.groups.all(), msg="create workflow group2 failed")
        print("===test_create_node_ok===")


class WorkFlowServiceTransmitTest(TestCase):
    def setUp(self):
        self.user1 = mommy.make(User)
        self.user2 = mommy.make(User)
        self.user3 = mommy.make(User)
        self.user4 = mommy.make(User)
        self.group1 = mommy.make(Group)
        self.group1.user_set.add(self.user1, self.user3)
        self.group2 = mommy.make(Group)
        self.group2.user_set.add(self.user1, self.user4)
        self.workflow = mommy.make(WorkFlow)
        self.approve_user = mommy.make(User)
        workflow = self.workflow
        code, name, is_start, is_end, logic_type = "demo1", "demo1", True, False, LogicType.logic_all
        users, groups, previous_node = [self.user1, self.user2], None, None
        node1 = WorkFlowService.create_node(workflow, code, name, is_start, is_end, logic_type, users,
                    groups, previous_node)
        code, name, is_start, is_end, logic_type = "demo2", "demo2", False, False, LogicType.logic_any
        users, groups, previous_node = None, None, node1
        node2 = WorkFlowService.create_node(workflow, code, name, is_start, is_end, logic_type, users,
                    groups, previous_node)
        code, name, is_start, is_end, logic_type = "demo3", "demo3", False, True, LogicType.logic_all
        users, groups, previous_node = None, [self.group1, self.group2], node2
        node3 = WorkFlowService.create_node(workflow, code, name, is_start, is_end, logic_type, users,
                    groups, previous_node)

    def test_get_start_node(self):
        start_node = WorkFlowService.get_start_node(self.workflow)
        self.assertTrue(start_node.is_start)
        print("===test_get_start_node_ok===")
        return start_node

    def test_start_workflow_instance(self):
        instance1 = WorkFlowService.start_workflow_instance(self.workflow, self.approve_user, self.user1)
        self.assertTrue(instance1.content_object == self.approve_user, msg="create workflow_instance failed")
        self.assertTrue(instance1.is_new, msg="create workflow_instance failed")
        instance2 = WorkFlowService.start_workflow_instance(self.workflow, self.approve_user, self.user1)
        self.assertTrue(WorkFlowInstance.objects.filter(is_new=False).count() == 1, msg="create workflow_instance failed")
        self.assertTrue(instance2.is_new, msg="create workflow_instance failed")
        print("===test_start_workflow_instance_ok===")
        return instance2

    def test_create_workflow_process(self):
        instance = self.test_start_workflow_instance()
        node = self.test_get_start_node()
        WorkFlowService.create_workflow_process(instance, node, todo=True)
        self.assertTrue(WorkFlowProcess.objects.filter(node=node).count() == 2, msg="create workflow_process failed")
        self.assertTrue(WorkFlowProcess.objects.filter(node=node).first().todo, msg="create workflow_process failed")
        node = node.next_node
        WorkFlowService.create_workflow_process(instance, node, todo=False, users=[self.user3, self.user4])
        self.assertTrue(WorkFlowProcess.objects.filter(node=node).count() == 2, msg="create workflow_process failed")
        self.assertTrue(WorkFlowProcess.objects.filter(node=node).first().todo == False, msg="create workflow_process failed")
        node = node.next_node
        WorkFlowService.create_workflow_process(instance, node, todo=False)
        self.assertTrue(WorkFlowProcess.objects.filter(node=node).count() == 3, msg="create workflow_process failed")
        print("===test_create_workflow_process===")

    def test_handle_workflow_process_agree_all(self):
        self.test_create_workflow_process()
        pro_type = WorkFlowProcessType.agree
        workflowprocesses = WorkFlowProcess.objects.filter(todo=True)
        workflowprocess0 = workflowprocesses[0]
        workflowprocess1 = workflowprocesses[1]
        workflowprocess = workflowprocess0
        current_node = workflowprocess.inst.current_node 
        WorkFlowService.handle_workflow_process(workflowprocess, pro_type, note="test_agree")
        self.assertTrue(workflowprocess.inst.current_node == current_node, msg="agree workflow_process all failed")
        self.assertTrue(workflowprocess.note == "test_agree", msg="agree workflow_process all failed")
        self.assertTrue(workflowprocess.todo == False, msg="agree workflow_process all failed")
        workflowprocess = workflowprocess1
        self.assertTrue(workflowprocess.todo)
        WorkFlowService.handle_workflow_process(workflowprocess, pro_type)
        self.assertTrue(workflowprocess.inst.current_node == current_node.next_node, msg="agree workflow_process all failed")
        self.assertTrue(WorkFlowProcess.objects.filter(node=current_node.next_node, todo=True).count() == 2, msg="agree workflow_process all failed")
        print("===test_handle_workflow_process_agree_all===")

    def test_handle_workflow_process_agree_any(self):
        self.test_handle_workflow_process_agree_all()
        workflowprocesses = WorkFlowProcess.objects.filter(todo=True)
        workflowprocess = workflowprocesses[0]
        pro_type = WorkFlowProcessType.agree
        current_node = workflowprocess.inst.current_node
        WorkFlowService.handle_workflow_process(workflowprocess, pro_type)
        self.assertTrue(workflowprocess.inst.current_node == current_node.next_node, msg="agree workflow_process any failed")
        self.assertTrue(WorkFlowProcess.objects.filter(node=current_node.next_node, todo=True).count() == 3, msg="agree workflow_process any failed")
        self.assertTrue(WorkFlowProcess.objects.filter(pro_type=WorkFlowProcessType.submit,
                node=current_node, todo=False).count() == 1, msg="agree workflow_process any failed")
        print("===test_handle_workflow_process_agree_any===")

    def test_handle_workflow_process_deny(self):
        self.test_handle_workflow_process_agree_any()
        workflowprocesses = WorkFlowProcess.objects.filter(todo=True)
        workflowprocess = workflowprocesses[0]
        pro_type = WorkFlowProcessType.deny
        current_node = workflowprocess.inst.current_node
        WorkFlowService.handle_workflow_process(workflowprocess, pro_type)
        self.assertTrue(workflowprocess.inst.current_node == current_node, msg="deny workflow_process failed")
        self.assertTrue(WorkFlowProcess.objects.filter(pro_type=pro_type, todo=False).count() == 1, msg="deny workflow_process failed")
        self.assertTrue(WorkFlowProcess.objects.filter(pro_type=WorkFlowProcessType.submit,
                node=current_node, todo=False).count() == 2, msg="deny workflow_process failed")
        print("===test_handle_workflow_process_deny===")