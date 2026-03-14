/** @odoo-module */

import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted , useState , useRef } = owl
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
export class LegalDashboard extends Component {
    /**
     * Setup method to initialize required services and register event handlers.
     */
	setup() {
	    this.companyService = useService("company");
		this.action = useService("action");
		this.orm = useService("orm");
		this.rpc = this.env.services.rpc
		this.lawyer_wise = useRef('lawyer_wise')
		this.state = useState({
            lawyer: 'admin',
            stage: 'null',
            month: 'null',
            cases_list: [],
            trial_list: [],
            evidence_list: [],
            lawyer_list:[],
            client_list: [],
            total_client: [],
            case_count: 0,
            invoice_count: 0,
            trials_count:0,
            evidences_count:0,
            lawyers_count:0,
            clients_count:0,
        });

		onWillStart(async () => {
		    await this.fetch_data();
		    await this._onWithoutFilter();
		});

		onMounted(() => {
		    var self =this;
		     rpc('/selection/field/lawyer')
            .then((result) => {
                var lawyer_list = result
                var  selection = self.lawyer_wise.el
                lawyer_list.forEach(lawyer => {
                    const option = document.createElement('option');
                    option.value = lawyer.id;
                    option.textContent = lawyer.name;
                    selection.appendChild(option);
                });
            })
		});
	}

	fetch_data(){
	    var self =this;
        var promise = rpc('/case/dashboard', {'current_company_id': this.companyService.currentCompany.id})
            .then((result) => {
                this.CaseManagementDashboard = result;
                self.state.total_client = result.clients_in_case
                //Graphs starts here
                google.charts.load('current', {
                    'packages': ['corechart']
                });
                google.charts.setOnLoadCallback(drawChart);
                function drawChart() {
                try{
                    //  Pie chart starts
                    var data = google.visualization.arrayToDataTable(result['case_category']);
                    var chart_options = {
                        'backgroundColor': 'transparent',
                        is3D: true
                    };
                    var chart = new google.visualization.PieChart(document.getElementById('pie_chart'));
                    chart.draw(data, chart_options);
                    // Pie chart end
                    //Donut chart start
                    var datas = google.visualization.arrayToDataTable(result.top_10_cases);
                    var options = {
                        'backgroundColor': 'transparent',
                        pieHole: 0.5
                    };
                    var charts = new google.visualization.PieChart(document.getElementById('donut_chart'));
                    charts.draw(datas, options);
                    //Donut chart end
                    //Linechart start
                    var datas = google.visualization.arrayToDataTable(result['data_list']);
                    var line_options = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        line: {
                            groupWidth: "40%"
                        },

                    };
                    var charts = new google.visualization.LineChart(document.getElementById('mygraph'));
                    charts.draw(datas, line_options);
                    //Linechart end
                    //Column chart start
                    var column_data = google.visualization.arrayToDataTable(result.stage_count);
                    var column_options = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        bar: {
                            groupWidth: "40%"
                        },
                    };
                    var column_chart = new google.visualization.ColumnChart(document.getElementById('column_graph'));
                    column_chart.draw(column_data, column_options);
                    //column chart end
                    }
                    catch (e) {
                        this.willStart()
                    }
                }
            });
	}
	_onWithoutFilter(){
        //	Values loaded without filter
	    var self = this;
	    rpc('/dashboard/without/filter',  {
	        'current_company_id': this.companyService.currentCompany.id
            })
            .then(function(value) {
                self.state.case_count = value.total_case;
                self.state.invoice_count = value.total_invoiced;
                self.state.trials_count = value.trials;
                self.state.evidences_count = value.evidences;
                self.state.lawyers_count = value.lawyers;
                self.state.clients_count = value.clients;
            });
	}
	_onchangeStageFilter(ev){
        //	Values loaded by changing the stage filter
        var self = this;
        var lawyer_filter = this.state.lawyer
        var stage_filter = this.state.stage
        var date_filter = this.state.month
        var data = {
            'stage': stage_filter,
            'lawyer': lawyer_filter || 'admin',
            'month_wise': date_filter
        };
       rpc('/dashboard/filter',  {
                'data': data,
                'current_company_id': this.companyService.currentCompany.id
            })
            .then(function(value) {
                self.state.cases_list = value.total_case
                self.state.trial_list = value.trials
                self.state.evidence_list = value.evidences
                self.state.lawyer_list = value.lawyers
                self.state.client_list = value.clients
                self.state.case_count = value.total_case.length;
                self.state.invoice_count = value.total_invoiced;
                self.state.trials_count = value.trials.length;
                self.state.evidences_count = value.evidences.length;
                self.state.lawyers_count = value.lawyers.length;
                self.state.clients_count = value.clients.length;
            });
	}
	_OnClickTotalClients() {
        let domain = [];
        if (this.state.client_list && this.state.client_list.length > 0) {
            domain = [['id', 'in', this.state.client_list]];
        } else {
            const currentCompanyId = this.companyService.currentCompany.id;
            domain = ['|',
                ['company_id', '=', false],
                ['company_id', '=', currentCompanyId]
            ];
        }
        this.action.doAction({
            name: _t("Total Clients"),
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: domain,
            context: { create: false },
            target: 'current',
        });
    }
	 _OnClickTotalTrials() {
        // Loading the total trials for the cases
        this.action.doAction({
            name: _t("Total Trials"),
            type: 'ir.actions.act_window',
            res_model: 'legal.trial',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: this.state.trial_list && this.state.trial_list.length > 0 ? [['id', 'in', this.state.trial_list]] : [],
            context: { create: false },
            target: 'current',
        });
    }
    _OnClickTotalLawyers() {
        // Load the lawyer lists
        let actionConfig = {
            name: _t("Total Lawyers"),
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            context: {
                create: false
            },
            target: 'current',
        };
        actionConfig.domain = this.state.lawyer_list.length > 0 ? [['id', 'in', this.state.lawyer_list]] : [['is_lawyer', '=', true]];
        this.action.doAction(actionConfig);
    }
     _OnClickTotalEvidences() {
        // Load the total evidences
        let actionConfig = {
            name: _t("Total Evidences"),
            type: 'ir.actions.act_window',
            res_model: 'legal.evidence',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            context: {
                create: false
            },
            target: 'current',
        };
        actionConfig.domain = this.state.evidence_list && this.state.evidence_list.length > 0 ? [['id', 'in', this.state.evidence_list]] : [] ;
        this.action.doAction(actionConfig);
    }
	_OnClickTotalCase() {
        // Load the total case
        let actionConfig = {
            name: _t("Total Cases"),
            type: 'ir.actions.act_window',
            res_model: 'case.registration',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            context: {
                create: false
            },
            target: 'current',
        };
        actionConfig.domain = this.state.cases_list && this.state.cases_list.length > 0  ? [['id', 'in', this.state.cases_list]] : [];
        this.action.doAction(actionConfig);
    }
}
LegalDashboard.template = "CaseDashBoard"
registry.category("actions").add("case_dashboard_tags", LegalDashboard)
