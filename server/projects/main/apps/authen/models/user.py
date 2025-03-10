# # -*- coding: utf-8 -*-
# Copyright (c) 2021-2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================

"""用户模型
"""
# 原生 import
import logging

# 第三方 import
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm

# 项目内 import
from apps.base.basemodel import BasePerm, CDBaseModel

logger = logging.getLogger(__name__)


class Organization(CDBaseModel, BasePerm):
    """团队
    """

    class PermissionNameEnum:
        VIEW_ORG_PERM = "view_organization"
        CHANGE_ORG_PERM = "change_organization"

    class StatusEnum:
        ACTIVE = 1
        DISACTIVE = 2
        EXPIRED = 3
        FORBIDEN = 99

    STATUSENUM_CHOICES = (
        (StatusEnum.ACTIVE, "已激活"),
        (StatusEnum.DISACTIVE, "待激活"),
        (StatusEnum.EXPIRED, "已过期"),
        (StatusEnum.FORBIDEN, "禁止")
    )

    class LevelEnum:
        NORMAL = 1
        VIP = 2
        SUPER_VIP = 3

    LEVELENUM_CHOICES = (
        (LevelEnum.NORMAL, "普通团队"),
        (LevelEnum.VIP, "VIP团队"),
        (LevelEnum.SUPER_VIP, "超级VIP团队"),
    )

    LEVEL_PROJECT_TEAM_COUNT_CHOICES = (
        (LevelEnum.NORMAL, 2),
        (LevelEnum.VIP, 20),
        (LevelEnum.SUPER_VIP, 9999),
    )

    LEVEL_REPO_TEAM_COUNT_CHOICES = (
        (LevelEnum.NORMAL, 3),
        (LevelEnum.VIP, 10),
        (LevelEnum.SUPER_VIP, 9999),
    )

    org_sid = models.CharField(max_length=64, help_text="组织短编号", unique=True)
    name = models.CharField(help_text="组织名称", max_length=255)
    address = models.CharField(help_text="组织地址", max_length=255, null=True, blank=True)
    description = models.TextField(help_text="团队描述信息", null=True, blank=True)
    certificated = models.BooleanField(help_text="组织认证", default=False)
    owner = models.CharField(help_text="组织负责人", max_length=255, null=True, blank=True)
    business_license = models.CharField(help_text="营业执照编号", max_length=64, null=True, blank=True)
    tel_number = models.CharField(max_length=32, help_text="组织手机号", null=True, blank=True)
    status = models.IntegerField(help_text="组织状态", default=StatusEnum.DISACTIVE, choices=STATUSENUM_CHOICES)
    level = models.IntegerField(help_text="组织级别", default=LevelEnum.NORMAL, choices=LEVELENUM_CHOICES)
    db_key = models.CharField(max_length=32, help_text="关联数据库", default="default")

    def validate_org_checked(self):
        """判断当前团队是否已经审核通过
        """
        if self.status > self.StatusEnum.ACTIVE:
            return False
        else:
            return True

    def _get_group(self, perm):
        permission_choices = dict(self.PERMISSION_CHOICES)
        group_name = "_".join(("org", str(self.id), permission_choices[perm]))
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            if perm == self.PermissionEnum.ADMIN:
                assign_perm(self.PermissionNameEnum.CHANGE_ORG_PERM, group, self)
            assign_perm(self.PermissionNameEnum.VIEW_ORG_PERM, group, self)
        return group

    def __unicode__(self):
        return "%s" % self.org_sid

    def __str__(self):
        return self.__unicode__()


class OrganizationPermissionApply(models.Model):
    """团队权限申请表
    """

    class ApplyStatusEnum:
        CHECKING = 1
        CHECKED = 2
        CANCELED = 3

    APPLYSTATUSENUM_CHOICES = (
        (ApplyStatusEnum.CHECKING, "申请中"),
        (ApplyStatusEnum.CHECKED, "审批完成"),
        (ApplyStatusEnum.CANCELED, "取消申请")
    )

    class CheckResultEnum:
        PASS = 1
        NO_PASS = 2

    CHECKRESULTENUM_CHOICES = (
        (CheckResultEnum.PASS, "审批通过"),
        (CheckResultEnum.NO_PASS, "审批不通过"),
    )

    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, help_text="申请团队")
    applicant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="申请人")
    apply_time = models.DateTimeField(auto_now_add=True, help_text="申请时间")
    apply_msg = models.CharField(max_length=255, help_text="申请理由")
    status = models.IntegerField(help_text="申请状态", default=ApplyStatusEnum.CHECKING, choices=APPLYSTATUSENUM_CHOICES)
    checker = models.ForeignKey(User, related_name="+", on_delete=models.SET_NULL, null=True, blank=True)
    check_result = models.IntegerField(help_text="审批结果", null=True, blank=True, choices=CHECKRESULTENUM_CHOICES)
    check_remark = models.CharField(max_length=255, help_text="审批备注", null=True, blank=True)
    check_time = models.DateTimeField(help_text="审批时间", null=True, blank=True)

    def validate_apply_pass(self):
        """判断当前申请单是否审核通过
        """
        return self.status == self.ApplyStatusEnum.CHECKED and self.check_result == self.CheckResultEnum.PASS

    def is_checking(self):
        """判断申请单是否正在审核中
        """
        return self.status == self.ApplyStatusEnum.CHECKING

    def is_checked_and_no_pass(self):
        """判断申请单 是否已审核完成，但未通过
        """
        return self.status == self.ApplyStatusEnum.CHECKED and self.check_result != self.CheckResultEnum.PASS


class CodeDogUser(models.Model):
    """CodeDog 用户
    """

    class StatusEnum:
        ACTIVE = 1
        DISACTIVE = 2
        EXPIRED = 3
        FORBIDEN = 99

    STATUSENUM_CHOICES = (
        (StatusEnum.ACTIVE, "已激活"),
        (StatusEnum.DISACTIVE, "待激活"),
        (StatusEnum.EXPIRED, "已过期"),
        (StatusEnum.FORBIDEN, "禁止")
    )

    class LevelEnum:
        NORMAL = 1
        VIP = 2
        SUPER_VIP = 3

    LEVELENUM_CHOICES = (
        (LevelEnum.NORMAL, "普通用户"),
        (LevelEnum.VIP, "VIP用户"),
        (LevelEnum.SUPER_VIP, "超级VIP用户"),
    )

    LEVEL_ORG_COUNT_CHOICES = (
        (LevelEnum.NORMAL, 3),
        (LevelEnum.VIP, 10),
        (LevelEnum.SUPER_VIP, 9999),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    nickname = models.CharField(max_length=32, help_text="用户昵称")
    chinese_name = models.CharField(max_length=32, help_text="用户中文名", null=True, blank=True)
    status = models.IntegerField(help_text="用户状态", default=StatusEnum.ACTIVE, choices=STATUSENUM_CHOICES)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    avatar = models.URLField(verbose_name="头像地址", blank=True, null=True)
    tel_number = models.CharField(max_length=32, help_text="用户手机号", null=True, blank=True)
    level = models.IntegerField(help_text="用户级别", default=LevelEnum.NORMAL, choices=LEVELENUM_CHOICES)
    # 待废弃
    org = models.ForeignKey(Organization, help_text="组织信息", on_delete=models.SET_NULL, null=True, blank=True)

    def validate_codedog_user_checked(self):
        """判断当前用户是否已经审核通过
        """
        if self.status > self.StatusEnum.ACTIVE:
            return False
        else:
            return True

    def __str__(self):
        return self.nickname


# 信号接收函数，每当新建 User 实例时自动调用
@receiver(post_save, sender=User)
def create_codedog_user(sender, instance, created, **kwargs):
    if created:
        CodeDogUser.objects.get_or_create(user=instance, defaults={"nickname": instance.username})


@receiver(post_save, sender=User)
def save_codedog_user(sender, instance, **kwargs):
    try:
        instance.codedoguser.save()
    except CodeDogUser.DoesNotExist:
        pass


class CodeDogUserPermissionApply(models.Model):
    """CodeDog用户权限申请表
    """

    class ApplyStatusEnum:
        CHECKING = 1
        CHECKED = 2
        CANCELED = 3

    APPLYSTATUSENUM_CHOICES = (
        (ApplyStatusEnum.CHECKING, "申请中"),
        (ApplyStatusEnum.CHECKED, "审批完成"),
        (ApplyStatusEnum.CANCELED, "取消申请")
    )

    class CheckResultEnum:
        PASS = 1
        NO_PASS = 2

    CHECKRESULTENUM_CHOICES = (
        (CheckResultEnum.PASS, "审批通过"),
        (CheckResultEnum.NO_PASS, "审批不通过"),
    )

    applicant = models.ForeignKey(CodeDogUser, on_delete=models.SET_NULL, null=True, blank=True)
    apply_time = models.DateTimeField(auto_now_add=True, help_text="申请时间")
    apply_msg = models.CharField(max_length=255, help_text="申请理由")
    status = models.IntegerField(help_text="申请状态", default=ApplyStatusEnum.CHECKING, choices=APPLYSTATUSENUM_CHOICES)
    checker = models.ForeignKey(CodeDogUser, related_name="+", on_delete=models.SET_NULL, null=True, blank=True)
    check_result = models.IntegerField(help_text="审批结果", null=True, blank=True, choices=CHECKRESULTENUM_CHOICES)
    check_remark = models.CharField(max_length=255, help_text="审批备注", null=True, blank=True)
    check_time = models.DateTimeField(help_text="审批时间", null=True, blank=True)

    def validate_apply_pass(self):
        """判断当前申请单是否审核通过
        """
        return self.status == self.ApplyStatusEnum.CHECKED and self.check_result == self.CheckResultEnum.PASS
