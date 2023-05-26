import datetime
from dateutil.relativedelta import relativedelta

class compliancePlan:
    def __init__(self) -> None:
        pass

    def selfInsured(clientFundingTag:str):
        if "self" in clientFundingTag.lower():
            return True
        else:
            return False
        
    def fullyInsured(clientFundingTag:str):
        if "fully" in clientFundingTag.lower():
            return True
        else:
            return False
        
    def applicableLargeEmployer(clientALE:str):
        if "applicable large group" in clientALE.lower():
            return True
        else:
            return False
    
    def fullTimeEmployeeThreshold(clientFTEThreshold:int,templateFTEThreshold:int):
        if clientFTEThreshold >= templateFTEThreshold:
            return True
        else:
            return False
    
    def templateProceedLogic(conditional:list,fte:int):
        if (not conditional) and (not fte):
            return True
        elif (not conditional) and (fte):
            return [fte]
        elif (conditional) and (not fte):
            return [conditional]
        elif (conditional) and (fte):
            return [conditional,fte]
        else:
            return False
    
    def singleConditionEvaluation(conditionItems:list,clientFundingTag:str,clientALE:str,clientFTEThreshold:int,templateFTEThreshold:int):
        if len(conditionItems) == 1:
            if isinstance(conditionItems[0],str):
                if "fully" in conditionItems[0].lower():
                    return compliancePlan.fullyInsured(
                        clientFundingTag=clientFundingTag
                        )
                elif "self" in conditionItems[0].lower():
                    return compliancePlan.selfInsured(
                        clientFundingTag=clientFundingTag
                    )
                elif "applicable large group" in conditionItems[0].lower():
                    return compliancePlan.applicableLargeEmployer(
                        clientALE=clientALE
                    )
            elif isinstance(conditionItems[0],int):
                return compliancePlan.fullTimeEmployeeThreshold(
                    clientFTEThreshold=clientFTEThreshold,
                    templateFTEThreshold=templateFTEThreshold
                )
        else:
            raise Exception("Something Failed in SingleConditionEvaluation")
    
    def multipleConditionEvaluation(conditionItems:list,clientFundingTag:str,clientALE:str,clientFTEThreshold:int,templateFTEThreshold:int):
        return_array = []
        if len(conditionItems) > 1:
            for i in conditionItems:
                return_array.append(
                    compliancePlan.singleConditionEvaluation(
                        conditionItems=[i],
                        clientFundingTag=clientFundingTag,
                        clientALE=clientALE,
                        clientFTEThreshold=clientFTEThreshold,
                        templateFTEThreshold=templateFTEThreshold
                    )
                )
            return return_array
        else:
            raise Exception("Soemthing Failed in MultipleConditionEvaluation")


    def conditionRun(conditionItems:list,clientFundingTag:str,clientALE:str,clientFTEThreshold:int,templateFTEThreshold:int):
        if len(conditionItems) == 1:
            return compliancePlan.singleConditionEvaluation(
                conditionItems=conditionItems,
                clientFundingTag=clientFundingTag,
                clientALE=clientALE,
                clientFTEThreshold=clientFTEThreshold,
                templateFTEThreshold=templateFTEThreshold
            )
        elif len(conditionItems) > 1:
            return_array = compliancePlan.multipleConditionEvaluation(
                conditionItems=conditionItems,
                clientFundingTag=clientFundingTag,
                clientALE=clientALE,
                clientFTEThreshold=clientFTEThreshold,
                templateFTEThreshold=templateFTEThreshold
            )
            if all(return_array):
                return True
            else:
                return False

    def returnComplianceDueDate(datesDictionary:dict,complianceRenewalDate:datetime):
        if not datesDictionary["calendarDueDate"]:
            if not datesDictionary["monthsPostRenewal"]:
                if not datesDictionary["daysPostRenewal"]:
                    return None
                elif datesDictionary["daysPostRenewal"]:
                    due_date = complianceRenewalDate + relativedelta(days=datesDictionary["daysPostRenewal"])
                    return due_date
            elif datesDictionary["monthsPostRenewal"]:
                due_date = complianceRenewalDate + relativedelta(months=datesDictionary["monthsPostRenewal"])
                return due_date
        elif datesDictionary["calendarDueDate"]:
            if isinstance(datesDictionary["calendarDueDate"],str):
                format_str = '%m/%d/%Y'
                datetime_obj = datetime.datetime.strptime(datesDictionary["calendarDueDate"], format_str)
            return datetime_obj
    
    def returnNavaDueDate(datesDictionary:dict,complianceRenewalDate:datetime,calendarDueDate=None):
        if not datesDictionary["calendarDueDateCalc"]:
            if not datesDictionary["monthsPostRenewal"]:
                due_date = complianceRenewalDate + relativedelta(days=datesDictionary["daysPostRenewal"])
                return due_date
            elif datesDictionary["monthsPostRenewal"]:
                due_date = complianceRenewalDate + relativedelta(months=datesDictionary["monthsPostRenewal"])
                return due_date
        elif (datesDictionary["calendarDueDateCalc"]) and (isinstance(calendarDueDate,str)):
            format_str = '%m/%d/%Y'
            datetime_obj = datetime.datetime.strptime(calendarDueDate, format_str)
            due_date = datetime_obj - relativedelta(months=datesDictionary["calendarDueDateCalc"])
            return due_date
    
    def complianceRenewalDate(renewalDate:str):
        if isinstance(renewalDate,str):
            format_str = '%Y-%m-%d'
            datetime_obj = datetime.datetime.strptime(renewalDate, format_str)
            compliance_date = datetime_obj - relativedelta(years=1)
            return compliance_date
        elif isinstance(renewalDate,list):
            renewal_date = renewalDate[0]
            format_str = '%Y-%m-%d'
            datetime_obj = datetime.datetime.strptime(renewalDate, format_str)
            compliance_date = datetime_obj - relativedelta(years=1)
            return compliance_date