from datetime import datetime
from dateutil.relativedelta import relativedelta


class servicePlan:
    def __init__(self) -> None:
        pass

    def groupSize(logicGroupSize:str,clientGroupSize:str):
        if clientGroupSize in logicGroupSize:
            return True
        else:
            return False
        
    def conditionalTag(logicConditionals,clientConditionals):
        if not logicConditionals:
            return True
        elif logicConditionals:
            bucketConditionalsList = logicConditionals.split(", ")
            if not clientConditionals:
                return False
            elif clientConditionals and isinstance(clientConditionals,list):
                # clientConditionalsList = clientConditionals.split(", ")
                result = [elem for elem in clientConditionals if elem in bucketConditionalsList]
                if result:
                    return True
                else:
                    return False
    def fundingTag(logicFundingTag:str,clientFundingTag:str):
        if not logicFundingTag:
            return False
        elif logicFundingTag:
            taskFundingTagList = logicFundingTag.split(", ")
            if clientFundingTag in taskFundingTagList:
                return True
            else:
                return False
    
    def dateTimeNBPDate(date_datetime:datetime,time_length:int,time_unit:str):
        if time_unit == "days":
            return date_datetime + relativedelta(days=time_length)
        elif time_unit == "months":
            return date_datetime + relativedelta(months=time_length)

    def dateTimeDropDeadDate(bucketReturnDate:datetime,time_length:int,time_unit:str):
        if time_unit == "days":
            return bucketReturnDate + relativedelta(days=time_length)
        elif time_unit == "months":
            return bucketReturnDate + relativedelta(months=time_length)
    
    def bucketDateLogic(bucket:dict,renewal_date:str,group_size:str,bor_date:str,client_conditionals:list):

        acceptable_group_list = ["Small Group","Large Group"]
        if group_size not in acceptable_group_list:
            raise ValueError("Invalid Group Size. Expected one of: %s" % acceptable_group_list)
        
        if not bucket["bucket_metadata"]["date_logic"]:
            return False,False
        
        elif bucket["bucket_metadata"]["date_logic"]:
            # DATE PRE-PROCESSING
                # NBP PROCESSING
            nbp_time_length = bucket["bucket_metadata"]["date_logic"][group_size]["NBP Date"]
            nbp_time_unit = bucket["bucket_metadata"]["date_logic"][group_size]["nbp_time_unit"]    
                # DROP DEAD PROCESSING
            drop_dead_time_length = bucket["bucket_metadata"]["date_logic"][group_size]["Drop Dead Date"]
            drop_dead_time_unit = bucket["bucket_metadata"]["date_logic"][group_size]["drop_dead_time_unit"]

            if bucket["service_journey_bucket_id"] == "recCXYRH4qxmbjDLv":
                if "Onboarding" in client_conditionals:
                    bor_date_formatted = datetime.strptime(bor_date,'%Y-%m-%d')
                    nbp_date = servicePlan.dateTimeNBPDate(date_datetime=bor_date_formatted,time_length=nbp_time_length,time_unit=nbp_time_unit)
                    drop_dead_date = servicePlan.dateTimeDropDeadDate(bucketReturnDate=nbp_date,time_length=drop_dead_time_length,time_unit=drop_dead_time_unit)
                    return nbp_date,drop_dead_date
                else:
                    return False, False
            else:
                renewal_date_formatted = datetime.strptime(renewal_date,'%Y-%m-%d')
                nbp_date = servicePlan.dateTimeNBPDate(date_datetime=renewal_date_formatted,time_length=nbp_time_length,time_unit=nbp_time_unit)
                drop_dead_date = servicePlan.dateTimeDropDeadDate(bucketReturnDate=nbp_date,time_length=drop_dead_time_length,time_unit=drop_dead_time_unit)
                return nbp_date,drop_dead_date
        
    def bucketLogic(bucket:dict,group_size:str,clientConditionals:list,renewal_date:str,bor_date:str):
        evaluation_array = [
            servicePlan.groupSize(logicGroupSize=bucket["bucket_metadata"]["group_size"],clientGroupSize=group_size),
            servicePlan.conditionalTag(logicConditionals=bucket["bucket_metadata"]["conditional_tag"],clientConditionals=clientConditionals)
        ]
        if all(evaluation_array): # if everything is true in return array & if we have TRUTHY variables for return dates, let's rock!
            nbp_date, drop_dead_date = servicePlan.bucketDateLogic(bucket=bucket,renewal_date=renewal_date,group_size=group_size,bor_date=bor_date,client_conditionals=clientConditionals)
            if nbp_date and drop_dead_date:
                return nbp_date,drop_dead_date
            elif not nbp_date and not drop_dead_date:
                nbp_date = None
                drop_dead_date = None
                return nbp_date,drop_dead_date
            
    def toAirtableDates(date_time_object:datetime):
        if not date_time_object:
            return None
        else:
            return date_time_object.strftime('%Y-%m-%d')

    def returnQuarter(renewal_date_formatted:datetime):
        renewal_date_year = renewal_date_formatted.year
        renewal_date_month = renewal_date_formatted.month
        if renewal_date_month in (1,2,3):
            return datetime(year=renewal_date_year-1,month=11,day=15)
        elif renewal_date_month in (4,5,6):
            return datetime(year=renewal_date_year,month=2,day=15) 
        elif renewal_date_month in (7,8,9):
            return datetime(year=renewal_date_year,month=5,day=15)
        else:
            return datetime(year=renewal_date_year,month=8,day=15)

    def return75Days(renewal_date_formatted:datetime):
        return renewal_date_formatted - relativedelta(days=75)

    def milestoneDateLogic(milestone:dict,bucket_due_date:datetime,group_size:str,renewal_date:str):
        # IF NO DATE LOGIC, RETURN NONE
        if not milestone["milestone_metadata"]["date_logic"]:
            return None
        else:
            milestone_date_logic = milestone["milestone_metadata"]["date_logic"][group_size]
            # if the milestone date logic is a bucket dependency, return the bucket nbp due date that we sent with it
            if "bucket_dependency" in milestone_date_logic.keys():
                return bucket_due_date
            elif "custom_date" in milestone_date_logic.keys():
                renewal_date_formatted = datetime.strptime(renewal_date,'%Y-%m-%d')
                return servicePlan.return75Days(renewal_date_formatted=renewal_date_formatted)

    def milestoneLogicNoDates(milestone:dict,clientConditionals:list,group_size:str):
        evaluation_array = [
            servicePlan.groupSize(logicGroupSize=milestone["milestone_metadata"]["group_size"],clientGroupSize=group_size),
            servicePlan.conditionalTag(logicConditionals=milestone["milestone_metadata"]["conditional_tag"],clientConditionals=clientConditionals)
        ]
        if all(evaluation_array):
            return True
        else:
            return False

    def milestoneLogicNoDependency(milestone:dict,clientConditionals:list,bucketNBP:datetime,group_size:str,renewal_date:str):
        evaluation_array = [
            servicePlan.groupSize(logicGroupSize=milestone["milestone_metadata"]["group_size"],clientGroupSize=group_size),
            servicePlan.conditionalTag(logicConditionals=milestone["milestone_metadata"]["conditional_tag"],clientConditionals=clientConditionals)
        ]
        if all(evaluation_array):
            return servicePlan.milestoneDateLogic(milestone=milestone,bucket_due_date=bucketNBP,group_size=group_size,renewal_date=renewal_date)
        elif not all(evaluation_array):
            return None
        
    def milestoneContinuationLogic(milestone:dict):
        if len(milestone["milestone_metadata"]["date_logic"].keys()) > 1:
            if "milestone_dependency" in milestone["milestone_metadata"]["date_logic"]["Large Group"]:
                return False
            else:
                return True
        else:
            return False

    def milestoneDependencyCustom(milestone:dict,group_size:str,bucket_due_date:datetime,renewal_date:str,clientConditionals:list,milestone_computed:list):
        evaluation_array = [
            servicePlan.groupSize(logicGroupSize=milestone["milestone_metadata"]["group_size"],clientGroupSize=group_size),
            servicePlan.conditionalTag(logicConditionals=milestone["milestone_metadata"]["conditional_tag"],clientConditionals=clientConditionals)
        ]
        if all(evaluation_array):
            # print(milestone["milestone_metadata"]["date_logic"][group_size].keys())
            if "custom_date" in milestone["milestone_metadata"]["date_logic"][group_size].keys():
                return servicePlan.milestoneDateLogic(milestone=milestone,bucket_due_date=bucket_due_date,group_size=group_size,renewal_date=renewal_date)
            elif "milestone_dependency" in milestone["milestone_metadata"]["date_logic"][group_size].keys():
                for l in range(len(milestone_computed)):
                    if milestone["milestone_metadata"]["date_logic"][group_size]["milestone_dependency"] == milestone_computed[l]["milestone_id"]:
                        due_date = servicePlan.dateTimeNBPDate(
                            date_datetime=milestone_computed[l]["due_date"],
                            time_length=milestone["milestone_metadata"]["date_logic"][group_size]["time_length"],
                            time_unit=milestone["milestone_metadata"]["date_logic"][group_size]["time_unit"]
                        )

                        return due_date
        else:
            return False
        
    def taskLogic(task:dict,group_size:str,funding_tag:str):
        if not task:
            return False
        elif task:
            evaluation_array = [
                servicePlan.groupSize(logicGroupSize=task["task_metadata"]["group_size"],clientGroupSize=group_size),
                servicePlan.fundingTag(logicFundingTag=task["task_metadata"]["funding_tag"],clientFundingTag=funding_tag)
            ]
            if all(evaluation_array):
                return True
            else:
                return False


