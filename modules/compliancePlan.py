import datetime
from dateutil.relativedelta import relativedelta

class CompliancePlan:
    def __init__(self):
        pass

    def selfInsured(self,clientFundingTag:str):
        if "self" in clientFundingTag.lower():
            return True
        else:
            return False
        
    def fullyInsured(self,clientFundingTag:str):
        if "fully" in clientFundingTag.lower():
            return True
        else:
            return False
        
    def applicableLargeEmployer(self,clientALE:str):
        if "applicable large group" in clientALE.lower():
            return True
        else:
            return False
    
    def fullTimeEmployeeThreshold(self,clientFTEThreshold:int,templateFTEThreshold:int):
        if clientFTEThreshold >= templateFTEThreshold:
            return True
        else:
            return False
    
    def templateProceedLogic(self,conditional:list,fte:int):
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
    
    def singleConditionEvaluation(self,conditionItems:list,clientFundingTag:str,clientALE:str,clientFTEThreshold:int,templateFTEThreshold:int):
        if len(conditionItems) == 1:
            if isinstance(conditionItems[0],str):
                if "fully" in conditionItems[0].lower():
                    return self.fullyInsured(
                        clientFundingTag=clientFundingTag
                        )
                elif "self" in conditionItems[0].lower():
                    return self.selfInsured(
                        clientFundingTag=clientFundingTag
                    )
                elif "applicable large group" in conditionItems[0].lower():
                    return self.applicableLargeEmployer(
                        clientALE=clientALE
                    )
            elif isinstance(conditionItems[0],int):
                return self.fullTimeEmployeeThreshold(
                    clientFTEThreshold=clientFTEThreshold,
                    templateFTEThreshold=templateFTEThreshold
                )
        else:
            raise Exception("Something Failed in SingleConditionEvaluation")
    
    def multipleConditionEvaluation(self,conditionItems:list,clientFundingTag:str,clientALE:str,clientFTEThreshold:int,templateFTEThreshold:int):
        return_array = []
        if len(conditionItems) > 1:
            for i in conditionItems:
                return_array.append(
                    self.singleConditionEvaluation(
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


    def conditionRun(self,conditionItems:list,clientFundingTag:str,clientALE:str,clientFTEThreshold:int,templateFTEThreshold:int):
        if len(conditionItems) == 1:
            return self.singleConditionEvaluation(
                conditionItems=conditionItems,
                clientFundingTag=clientFundingTag,
                clientALE=clientALE,
                clientFTEThreshold=clientFTEThreshold,
                templateFTEThreshold=templateFTEThreshold
            )
        elif len(conditionItems) > 1:
            return_array = self.multipleConditionEvaluation(
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

    def returnComplianceDueDate(self,datesDictionary:dict,complianceRenewalDate:datetime):
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
    
    def returnNavaDueDate(self,datesDictionary:dict,complianceRenewalDate:datetime,calendarDueDate=None):
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
    
    def complianceRenewalDate(self,renewalDate:str):
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