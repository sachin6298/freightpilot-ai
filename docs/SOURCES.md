# Sources and Reference Links

Recheck these links before final submission because hackathon rules and developer documentation can change.

## PayPal AI Hackathon
- Official PayPal announcement (Sept. 30, 2026): https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/
- Devpost project page: https://paypalaihackathon.devpost.com/
- Official rules and submission requirements: https://paypalaihackathon.devpost.com/rules
- Devpost resources: https://paypalaihackathon.devpost.com/resources

The official rules state that projects should integrate the PayPal developer platform in Sandbox with an AI tool/model/platform; a functional demo, public open-source repository/license, and a public YouTube demo video under three minutes are required. The official contest is open-ended rather than providing fixed problem statements.

## PayPal developer resources
- Current REST API resources: https://developer.paypal.com/api/rest/current-resources/
- Orders v2 API: https://developer.paypal.com/docs/api/orders/v2/
- JavaScript SDK: https://developer.paypal.com/sdk/js/
- Webhooks overview: https://developer.paypal.com/api/rest/webhooks
- PayPal Developer portal: https://developer.paypal.com/

## India account caveat
- PayPal India help: receiving payments from Indian customers: https://www.paypal.com/in/cshelp/article/can-i-use-paypal-to-receive-payments-from-indian-customers-help1049

That PayPal help page says India users cannot receive domestic payments but can receive international payments in more than 25 currencies. This does not, by itself, confirm that every proposed freight/marketplace arrangement is eligible. Keep the hackathon demo in Sandbox and verify current terms before any production use.

## AI and security
Select an AI provider whose current API terms, pricing, usage limits, and data policy fit the project. Pin dependencies once tested. Use structured outputs/schema validation, minimize data sent to the model, and treat user-submitted quote text as untrusted data.
