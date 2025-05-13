# Case Quality Audit Report

## Case Information

**Case Number:** 2468513  
**Customer:** ABN Amro Bank N.V.  
**Product:** TIBCO BusinessWorks Container Edition 2.9.1  
**Severity:** Suggested Severity - Default-  
**Status:**   
**Created:** 2024-12-03 01:36:36  
**Closed:** 2024-12-24 01:27:49  
**Subject:** Application staying in impaired state while deploying to Azure DEV


## Case Summary

*Quick highlights of the case:*

Customer Bram Rekers reported an application in an impaired state during
deployment to Azure DEV within a Kubernetes Pod on December 3rd. The issue was
identified as missing shared modules in the EAR file by Hardik Bansal. After the
case was transferred to Sarthak Singhal, the customer resolved the issue
themselves by 'remavenizing' the application and shared modules on December
16th. The case was closed on December 24th.


## Quality Ratings

| Category | Rating | Description |
| --- | :---: | --- |
| Initial Response | 3/5 | The initial response was fairly prompt, asking for key information to start the troubleshooting process. However, it lacked personalization and didn't acknowledge the complexity of the issue described. The initial response could have been more proactive in suggesting initial troubleshooting steps. |
| Problem Diagnosis | 4/5 | The problem diagnosis was good. The support engineer (Hardik) correctly identified that the shared modules were not being included in the EAR file. Comparing the EAR files and pointing out the missing modules was a crucial step. |
| Technical Accuracy | 4/5 | The technical analysis regarding the missing shared modules was accurate. The suggestion to compare the EAR creation processes was also relevant. However, the support team did not provide specific guidance on how to fix the EAR creation process, which could have been more helpful. |
| Solution Quality | 3/5 | The solution was ultimately found by the customer ('remavenizing' the application and shared modules). While the support team helped to identify the root cause, they didn't directly provide the solution. The time taken to resolve was fairly long (12 days). |
| Communication | 3/5 | Communication was regular with multiple requests for information and a scheduled call. However, there were delays (acknowledged in the case notes). The communication could have been more proactive, with more regular updates even when there was no new information to share. Also, the case was transferred, which can be frustrating for customers. |
| Overall Experience | 3/5 | Overall, the support case was adequate but could be improved. The support team identified the core issue but didn't provide the final solution. The resolution time was also longer than ideal. Proactive communication and more specific guidance could have improved the overall experience. |


## Detailed Feedback

### Initial Response

The initial response was fairly prompt, asking for key information to start the
troubleshooting process. However, it lacked personalization and didn't
acknowledge the complexity of the issue described. The initial response could
have been more proactive in suggesting initial troubleshooting steps.

### Problem Diagnosis

The problem diagnosis was good. The support engineer (Hardik) correctly
identified that the shared modules were not being included in the EAR file.
Comparing the EAR files and pointing out the missing modules was a crucial step.

### Technical Accuracy

The technical analysis regarding the missing shared modules was accurate. The
suggestion to compare the EAR creation processes was also relevant. However, the
support team did not provide specific guidance on how to fix the EAR creation
process, which could have been more helpful.

### Solution Quality

The solution was ultimately found by the customer ('remavenizing' the
application and shared modules). While the support team helped to identify the
root cause, they didn't directly provide the solution. The time taken to resolve
was fairly long (12 days).

### Communication

Communication was regular with multiple requests for information and a scheduled
call. However, there were delays (acknowledged in the case notes). The
communication could have been more proactive, with more regular updates even
when there was no new information to share. Also, the case was transferred,
which can be frustrating for customers.

### Overall Assessment

Overall, the support case was adequate but could be improved. The support team
identified the core issue but didn't provide the final solution. The resolution
time was also longer than ideal. Proactive communication and more specific
guidance could have improved the overall experience.


## Recommendations

1. Provide more proactive suggestions for troubleshooting EAR creation issues related to Maven, including specific configuration settings to check
2. Document steps taken to analyze the EAR files and share the tools/methods used with the customer
3. When suggesting a call, propose multiple time slots instead of just requesting availability
4. Ensure a smooth handover when a case is transferred, with a brief summary of the previous interactions and findings
5. Include links to relevant TIBCO documentation or knowledge base articles in each response


*Report generated on: 2025-05-11 23:28:30*