# import functions_framework
from pyairtable import Table
from modules.servicePlan import ServicePlan
from modules.compliancePlan import CompliancePlan
from modules.airtableCreds import AirtableCreds

# @functions_framework.http
def service_plan(request):
    """
    Base state for adding a service plan (or service or compliance) for a client
    """
    # Get the Airtable Credentials from Bucket
    bucket_name = 'service-plan-credentials'
    file_name = 'airtable-creds.json'
    credentials = AirtableCreds(credentials_bucket=bucket_name,credentials_file=file_name).download_credentials()

    # Load the data
    data = request.get_json()
    request_type = data["request_type"]

    # # Instantiate the SerivcePlan Class
    service_plan = ServicePlan()
    compliance_plan = CompliancePlan()

    # Get the Required
    client_record_id = data['client_metadata']['client_id'][0]
    group_size = data['client_metadata']['group_size']
    funding_tag = data['client_metadata']['funding_tag']
    conditionals = data['client_metadata']['conditionals']
    renewal_date = data['client_metadata']['renewal_date']
    bor_date = data['client_metadata']['bor_date']
    ale_status = data['client_metadata']['ale_status']
    fte_num = data['client_metadata']['ftes']

    compliance_renewal_date = compliance_plan.complianceRenewalDate(renewalDate=renewal_date)

    ## AIRTABLE CONNECTIONS
    serviceBucketTable = Table(credentials["AUTH_TOKEN"],credentials["AIRTABLE_BASE"],credentials["SERVICE_BUCKET_TABLE"])
    # serviceBucketTable = Table('patUw9QIcMPeKLRh7.c2f17c4a308c3b57cd94ed95f3b2ecc0763fae82c4cb20cc13233e1d0feeeb54','appf7BT32bIwQNCpc','tblw9i2hYoEVWRvBL')
    serviceMilestoneTable = Table(credentials["AUTH_TOKEN"],credentials["AIRTABLE_BASE"],credentials["SERVICE_MILESTONE_TABLE"])
    # serviceMilestoneTable = Table('patUw9QIcMPeKLRh7.c2f17c4a308c3b57cd94ed95f3b2ecc0763fae82c4cb20cc13233e1d0feeeb54','appf7BT32bIwQNCpc','tblg7UkZucEjc9Fjy')
    serviceTaskTable = Table(credentials["AUTH_TOKEN"],credentials["AIRTABLE_BASE"],credentials["SERVICE_TASK_TABLE"])
    # serviceTaskTable = Table('patUw9QIcMPeKLRh7.c2f17c4a308c3b57cd94ed95f3b2ecc0763fae82c4cb20cc13233e1d0feeeb54','appf7BT32bIwQNCpc','tblIeqQPttrg4tGDE')
    complianceMilestoneTable = Table(credentials["AUTH_TOKEN"],credentials["AIRTABLE_BASE"],credentials["COMPLIANCE_MILESTONE_TABLE"])
    # complianceMilestoneTable = Table('patUw9QIcMPeKLRh7.c2f17c4a308c3b57cd94ed95f3b2ecc0763fae82c4cb20cc13233e1d0feeeb54','appf7BT32bIwQNCpc','tblprAQDS73qZJ5nx')
    complianceBucketTable = Table(credentials["AUTH_TOKEN"],credentials["AIRTABLE_BASE"],credentials["COMPLIANCE_BUCKET_TABLE"])
    # complianceBucketTable = Table('patUw9QIcMPeKLRh7.c2f17c4a308c3b57cd94ed95f3b2ecc0763fae82c4cb20cc13233e1d0feeeb54','appf7BT32bIwQNCpc','tblYyb3qGjoSRYPQk')

    ### BUILDING SCRIPT
    service_data = data["service_items"]
    compliance_data = data["compliance_items"]
    bucket_batch_list = []
    compliance_payload = []

    if request_type == "ServiceCompliance":
        for i in range(len(service_data)):

            service_bucket = service_plan.bucketLogic(bucket=service_data[i],group_size=group_size,clientConditionals=conditionals,renewal_date=renewal_date,bor_date=bor_date)

            if service_bucket:
                
                ## SET VARIABLES
                service_milestone = service_data[i]["bucket_milestones"]
                date_payload = []
                milestone_batch_list = []

                for v in range(len(service_milestone)):
                    return_task_payload = None

                    if not service_milestone[v]["milestone_metadata"]["date_logic"]:

                        if service_plan.milestoneLogicNoDates(milestone=service_milestone[v],clientConditionals=conditionals,group_size=group_size): # if there is no date logic for the milestone
                            
                            service_tasks = service_milestone[v]["milestone_tasks"]
                            task_payload_list = []
                            for z in range(len(service_tasks)):
                                if service_plan.taskLogic(task=service_tasks[z],group_size=group_size,funding_tag=funding_tag):
                                    task_payload = {
                                        "ServiceTrackingTasksTemplate": [service_tasks[z]["task_id"]]
                                    }
                                    task_payload_list.append(task_payload)
                            return_task_payload = serviceTaskTable.batch_create(task_payload_list,typecast=True)

                            milestone_payload = {
                                "ServiceTrackingMilestonesTemplate": [service_milestone[v]["milestone_id"]],
                                "Service Journey Tasks": [item["id"] for item in return_task_payload],
                                "Nava Best Practice Due Date": None,
                            }
                            milestone_batch_list.append(milestone_payload)


                    elif service_milestone[v]["milestone_metadata"]["date_logic"]:

                        if service_plan.milestoneContinuationLogic(milestone=service_milestone[v]):

                            due_date = service_plan.milestoneLogicNoDependency(milestone=service_milestone[v],clientConditionals=conditionals,bucketNBP=service_bucket[0],group_size=group_size,renewal_date=renewal_date)

                            if due_date:

                                service_tasks = service_milestone[v]["milestone_tasks"]
                                task_payload_list = []
                                for z in range(len(service_tasks)):
                                    if service_plan.taskLogic(task=service_tasks[z],group_size=group_size,funding_tag=funding_tag):
                                        task_payload = {
                                            "ServiceTrackingTasksTemplate": [service_tasks[z]["task_id"]]
                                        }
                                        task_payload_list.append(task_payload)
                                return_task_payload = serviceTaskTable.batch_create(task_payload_list,typecast=True)

                                milestone_payload = {
                                    "ServiceTrackingMilestonesTemplate": [service_milestone[v]["milestone_id"]],
                                    "Service Journey Tasks": [item["id"] for item in return_task_payload],
                                    "Nava Best Practice Due Date": service_plan.toAirtableDates(date_time_object=due_date)
                                }
                                milestone_batch_list.append(milestone_payload)
                                date_payload.append(
                                    {
                                        "milestone_id": service_milestone[v]["milestone_id"],
                                        "due_date": due_date
                                    }
                                )

                        if not service_plan.milestoneContinuationLogic(milestone=service_milestone[v]):
                            continue

                for v in range(len(service_milestone)):

                    if service_milestone[v]["milestone_metadata"]["date_logic"]:

                        if not service_plan.milestoneContinuationLogic(milestone=service_milestone[v]):

                            due_date = service_plan.milestoneDependencyCustom(
                                milestone=service_milestone[v],
                                group_size=group_size,
                                clientConditionals=conditionals,
                                bucket_due_date=service_bucket[0],
                                renewal_date=renewal_date,
                                milestone_computed=date_payload
                                )
                            if due_date:
                                service_tasks = service_milestone[v]["milestone_tasks"]
                                task_payload_list = []
                                for z in range(len(service_tasks)):
                                    if service_plan.taskLogic(task=service_tasks[z],group_size=group_size,funding_tag=funding_tag):
                                        task_payload = {
                                            "ServiceTrackingTasksTemplate": [service_tasks[z]["task_id"]]
                                        }
                                        task_payload_list.append(task_payload)
                                return_task_payload = serviceTaskTable.batch_create(task_payload_list,typecast=True)
                                
                                milestone_payload = {
                                    "ServiceTrackingMilestonesTemplate": [service_milestone[v]["milestone_id"]],
                                    "Service Journey Tasks": [item["id"] for item in return_task_payload],
                                    "Nava Best Practice Due Date": service_plan.toAirtableDates(date_time_object=due_date)
                                }
                                milestone_batch_list.append(milestone_payload)
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                return_milestones_payload = serviceMilestoneTable.batch_create(milestone_batch_list,typecast=True)
                bucket_payload = {
                    "Clients": client_record_id,
                    "ServiceTrackingBucketsTemplate": [
                        service_data[i]["service_journey_bucket_id"]
                        ],
                    "Nava Best Practice Due Date": service_plan.toAirtableDates(date_time_object=service_bucket[0]),
                    "Drop Dead Due Date": service_plan.toAirtableDates(date_time_object=service_bucket[1]),
                    "Service Journey Milestones": [item["id"] for item in return_milestones_payload],
                    "ServicePlanCreation": [data["record_id"]]
                }
                bucket_batch_list.append(bucket_payload)
            else:
                pass
        serviceBucketTable.batch_create(bucket_batch_list,typecast=True)

        for i in range(len(compliance_data)):

            conditional_list = compliance_data[i]["data"]["conditions"]["conditionEvaluation"]
            full_time_threshold = compliance_data[i]["data"]["conditions"]["fullTimeEmployeesThreshold"]
            checkStatus = compliance_plan.templateProceedLogic(conditional_list,full_time_threshold)
            
            if checkStatus and isinstance(checkStatus,bool):

                compliance_due_date = compliance_plan.returnComplianceDueDate(
                    datesDictionary=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"],
                    complianceRenewalDate=compliance_renewal_date
                )
                nava_due_date = compliance_plan.returnNavaDueDate(
                    datesDictionary=compliance_data[i]["data"]["dateLogic"]["navaComplianceDeadlines"],
                    complianceRenewalDate=compliance_renewal_date,
                    calendarDueDate=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"]["calendarDueDate"]
                )
                compliance_payload.append(
                    {
                        # "Clients": client_record_id,
                        "ComplianceMilestonesTemplate": [compliance_data[i]["recordId"]],
                        "Compliance Due Date": service_plan.toAirtableDates(date_time_object=compliance_due_date),
                        "Nava Due Date": service_plan.toAirtableDates(date_time_object=nava_due_date),
                        # "ServicePlanCreation": [data["record_id"]]
                    }
                )
            
            elif isinstance(checkStatus,list):
                evaluate_condition = compliance_plan.conditionRun(
                    conditionItems=checkStatus,
                    clientFundingTag=funding_tag,
                    clientALE=ale_status,
                    clientFTEThreshold=fte_num,
                    templateFTEThreshold=compliance_data[i]["data"]["conditions"]["fullTimeEmployeesThreshold"]
                )
                if evaluate_condition:
                    compliance_due_date = compliance_plan.returnComplianceDueDate(
                        datesDictionary=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"],
                        complianceRenewalDate=compliance_renewal_date
                    )
                    nava_due_date = compliance_plan.returnNavaDueDate(
                        datesDictionary=compliance_data[i]["data"]["dateLogic"]["navaComplianceDeadlines"],
                        complianceRenewalDate=compliance_renewal_date,
                        calendarDueDate=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"]["calendarDueDate"]
                    )
                    compliance_payload.append(
                        {
                            # "Clients": client_record_id,
                            "ComplianceMilestonesTemplate": [compliance_data[i]["recordId"]],
                            "Compliance Due Date": service_plan.toAirtableDates(date_time_object=compliance_due_date),
                            "Nava Due Date": service_plan.toAirtableDates(date_time_object=nava_due_date),
                            # "ServicePlanCreation": [data["record_id"]]
                        }
                    )
        compliance_milestone_records = complianceMilestoneTable.batch_create(compliance_payload,typecast=True)
        compliance_bucket_payload = {
            "Clients": [client_record_id],
            "ServicePlanCreation": [data["record_id"]],
            "Compliance Milestones": [item["id"] for item in compliance_milestone_records],
            "Compliance Bucket": "Compliance"
        }
        complianceBucketTable.create(compliance_bucket_payload,typecast=True)
        print(f'Created Service & Compliance for {client_record_id}, ServicePlan = {data["record_id"]}, RequestType = {data["request_type"]}')


    elif request_type == "ServiceOnly":
        for i in range(len(service_data)):

            service_bucket = service_plan.bucketLogic(bucket=service_data[i],group_size=group_size,clientConditionals=conditionals,renewal_date=renewal_date,bor_date=bor_date)

            if service_bucket:
                
                ## SET VARIABLES
                service_milestone = service_data[i]["bucket_milestones"]
                date_payload = []
                milestone_batch_list = []

                for v in range(len(service_milestone)):
                    return_task_payload = None

                    if not service_milestone[v]["milestone_metadata"]["date_logic"]:

                        if service_plan.milestoneLogicNoDates(milestone=service_milestone[v],clientConditionals=conditionals,group_size=group_size): # if there is no date logic for the milestone
                            
                            service_tasks = service_milestone[v]["milestone_tasks"]
                            task_payload_list = []
                            for z in range(len(service_tasks)):
                                if service_plan.taskLogic(task=service_tasks[z],group_size=group_size,funding_tag=funding_tag):
                                    task_payload = {
                                        "ServiceTrackingTasksTemplate": [service_tasks[z]["task_id"]]
                                    }
                                    task_payload_list.append(task_payload)
                            return_task_payload = serviceTaskTable.batch_create(task_payload_list,typecast=True)

                            milestone_payload = {
                                "ServiceTrackingMilestonesTemplate": [service_milestone[v]["milestone_id"]],
                                "Service Journey Tasks": [item["id"] for item in return_task_payload],
                                "Nava Best Practice Due Date": None,
                            }
                            milestone_batch_list.append(milestone_payload)


                    elif service_milestone[v]["milestone_metadata"]["date_logic"]:

                        if service_plan.milestoneContinuationLogic(milestone=service_milestone[v]):

                            due_date = service_plan.milestoneLogicNoDependency(milestone=service_milestone[v],clientConditionals=conditionals,bucketNBP=service_bucket[0],group_size=group_size,renewal_date=renewal_date)

                            if due_date:

                                service_tasks = service_milestone[v]["milestone_tasks"]
                                task_payload_list = []
                                for z in range(len(service_tasks)):
                                    if service_plan.taskLogic(task=service_tasks[z],group_size=group_size,funding_tag=funding_tag):
                                        task_payload = {
                                            "ServiceTrackingTasksTemplate": [service_tasks[z]["task_id"]]
                                        }
                                        task_payload_list.append(task_payload)
                                return_task_payload = serviceTaskTable.batch_create(task_payload_list,typecast=True)

                                milestone_payload = {
                                    "ServiceTrackingMilestonesTemplate": [service_milestone[v]["milestone_id"]],
                                    "Service Journey Tasks": [item["id"] for item in return_task_payload],
                                    "Nava Best Practice Due Date": service_plan.toAirtableDates(date_time_object=due_date)
                                }
                                milestone_batch_list.append(milestone_payload)
                                date_payload.append(
                                    {
                                        "milestone_id": service_milestone[v]["milestone_id"],
                                        "due_date": due_date
                                    }
                                )

                        if not service_plan.milestoneContinuationLogic(milestone=service_milestone[v]):
                            continue

                for v in range(len(service_milestone)):

                    if service_milestone[v]["milestone_metadata"]["date_logic"]:

                        if not service_plan.milestoneContinuationLogic(milestone=service_milestone[v]):

                            due_date = service_plan.milestoneDependencyCustom(
                                milestone=service_milestone[v],
                                group_size=group_size,
                                clientConditionals=conditionals,
                                bucket_due_date=service_bucket[0],
                                renewal_date=renewal_date,
                                milestone_computed=date_payload
                                )
                            if due_date:
                                service_tasks = service_milestone[v]["milestone_tasks"]
                                task_payload_list = []
                                for z in range(len(service_tasks)):
                                    if service_plan.taskLogic(task=service_tasks[z],group_size=group_size,funding_tag=funding_tag):
                                        task_payload = {
                                            "ServiceTrackingTasksTemplate": [service_tasks[z]["task_id"]]
                                        }
                                        task_payload_list.append(task_payload)
                                return_task_payload = serviceTaskTable.batch_create(task_payload_list,typecast=True)
                                
                                milestone_payload = {
                                    "ServiceTrackingMilestonesTemplate": [service_milestone[v]["milestone_id"]],
                                    "Service Journey Tasks": [item["id"] for item in return_task_payload],
                                    "Nava Best Practice Due Date": service_plan.toAirtableDates(date_time_object=due_date)
                                }
                                milestone_batch_list.append(milestone_payload)
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                return_milestones_payload = serviceMilestoneTable.batch_create(milestone_batch_list,typecast=True)
                bucket_payload = {
                    "Clients": client_record_id,
                    "ServiceTrackingBucketsTemplate": [
                        service_data[i]["service_journey_bucket_id"]
                        ],
                    "Nava Best Practice Due Date": service_plan.toAirtableDates(date_time_object=service_bucket[0]),
                    "Drop Dead Due Date": service_plan.toAirtableDates(date_time_object=service_bucket[1]),
                    "Service Journey Milestones": [item["id"] for item in return_milestones_payload],
                    "ServicePlanCreation": [data["record_id"]]
                }
                bucket_batch_list.append(bucket_payload)
            else:
                pass
        serviceBucketTable.batch_create(bucket_batch_list,typecast=True)
        print(f'Created Service Only for {client_record_id}, ServicePlan = {data["record_id"]}, RequestType = {data["request_type"]}')


    elif request_type == "ComplianceOnly":
        for i in range(len(compliance_data)):

            conditional_list = compliance_data[i]["data"]["conditions"]["conditionEvaluation"]
            full_time_threshold = compliance_data[i]["data"]["conditions"]["fullTimeEmployeesThreshold"]
            checkStatus = compliance_plan.templateProceedLogic(conditional_list,full_time_threshold)
            
            if checkStatus and isinstance(checkStatus,bool):

                compliance_due_date = compliance_plan.returnComplianceDueDate(
                    datesDictionary=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"],
                    complianceRenewalDate=compliance_renewal_date
                )
                nava_due_date = compliance_plan.returnNavaDueDate(
                    datesDictionary=compliance_data[i]["data"]["dateLogic"]["navaComplianceDeadlines"],
                    complianceRenewalDate=compliance_renewal_date,
                    calendarDueDate=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"]["calendarDueDate"]
                )
                compliance_payload.append(
                    {
                        # "Clients": client_record_id,
                        "ComplianceMilestonesTemplate": [compliance_data[i]["recordId"]],
                        "Compliance Due Date": service_plan.toAirtableDates(date_time_object=compliance_due_date),
                        "Nava Due Date": service_plan.toAirtableDates(date_time_object=nava_due_date),
                        # "ServicePlanCreation": [data["record_id"]]
                    }
                )
            
            elif isinstance(checkStatus,list):
                evaluate_condition = compliance_plan.conditionRun(
                    conditionItems=checkStatus,
                    clientFundingTag=funding_tag,
                    clientALE=ale_status,
                    clientFTEThreshold=fte_num,
                    templateFTEThreshold=compliance_data[i]["data"]["conditions"]["fullTimeEmployeesThreshold"]
                )
                if evaluate_condition:
                    compliance_due_date = compliance_plan.returnComplianceDueDate(
                        datesDictionary=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"],
                        complianceRenewalDate=compliance_renewal_date
                    )
                    nava_due_date = compliance_plan.returnNavaDueDate(
                        datesDictionary=compliance_data[i]["data"]["dateLogic"]["navaComplianceDeadlines"],
                        complianceRenewalDate=compliance_renewal_date,
                        calendarDueDate=compliance_data[i]["data"]["dateLogic"]["complianceDeadlines"]["calendarDueDate"]
                    )
                    compliance_payload.append(
                        {
                            # "Clients": client_record_id,
                            "ComplianceMilestonesTemplate": [compliance_data[i]["recordId"]],
                            "Compliance Due Date": service_plan.toAirtableDates(date_time_object=compliance_due_date),
                            "Nava Due Date": service_plan.toAirtableDates(date_time_object=nava_due_date),
                            # "ServicePlanCreation": [data["record_id"]]
                        }
                    )
                else:
                    pass
            else:
                pass
        compliance_milestone_records = complianceMilestoneTable.batch_create(compliance_payload,typecast=True)
        compliance_bucket_payload = {
            "Clients": [client_record_id],
            "ServicePlanCreation": [data["record_id"]],
            "Compliance Milestones": [item["id"] for item in compliance_milestone_records],
            "Compliance Bucket": "Compliance"
        }
        complianceBucketTable.create(compliance_bucket_payload,typecast=True)
        print(f'Created Compliance Only for {client_record_id}, ServicePlan = {data["record_id"]}, RequestType = {data["request_type"]}')

    return 'Done'