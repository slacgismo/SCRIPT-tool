import React, { Component } from "react";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogContentText from "@material-ui/core/DialogContentText";
import { withStyles } from "@material-ui/core/styles";
import axios from "axios";
import { ResultCharts } from "../Result/ResultCharts";
import { serverUrl } from "../Api/Server";
import {
    processResults,
    preprocessData,
    checkFlowerTaskStatus,
    exponentialBackoff,
} from "../Helpers/Helpers";

const FileDownload = require("js-file-download");

const styles = (theme) => ({
    container: {
        display: "flex",
        flexWrap: "wrap",
    },
    textField: {
        marginLeft: theme.spacing(1),
        marginRight: theme.spacing(1),
        width: 250,
    },
    dense: {
        marginTop: 19,
    },
    menu: {
        width: 200,
    },
    root: {
        width: 500,
        marginLeft: theme.spacing(1),
    },
    button: {
        margin: theme.spacing(1),
    },
    dialog: {
        maxWidth: 700,
    },
});

class AlgInputsCBA extends Component {
    constructor(props) {
        super(props);
        this.state = {
            openResult: false,
            shouldRender: false,
            openAlert: false,
            openDownloadCbaPopUp: false,
            alertTitle: "",
            alertDescription: "",
            profileName: "",
            profileNames: [],
            profileData: [],
            loadForecastResults: [],
            chartTitles: [],
        };
    }

    componentDidMount() {
        axios({
            url: `${serverUrl}/config/load_forecast`,
            method: "get",
        }).then(
            (res) => {
                const profiles = res.data;
                const profileNames = [];
                if (profiles.length > 0) {
                    for (var i = 0; i < profiles.length; i++) {
                        const profileNamesUnit = { name: "" };
                        profileNamesUnit.name = profiles[i]["config_name"];
                        profileNames.push(profileNamesUnit);
                    }
                    this.setState({
                        profileData: profiles,
                        profileNames: profileNames,
                        profileName: profileNames[0].name,
                    });
                }
            },
            (error) => {
                this.handleAlertOpen("Server Error", "Something went wrong");
            }
        );
    }

    getLoadForecastData = async () => {
        try {
            const lfRes = await axios.get(
                `${serverUrl}/algorithm/load_forecast`,
                {
                    params: {
                        config: this.state.profileName,
                    },
                }
            );
            const dataLoadForecast = [];
            for (var i = 0; i < lfRes.data.length; i++) {
                const dataLoadForecastUnit = {
                    residential_l1_load: "",
                    residential_l2_load: "",
                    residential_mud_load: "",
                    work_load: "",
                    fast_load: "",
                    public_l2_load: "",
                    total_load: "",
                };
                dataLoadForecastUnit.residential_l1_load =
                    lfRes.data[i].residential_l1_load;
                dataLoadForecastUnit.residential_l2_load =
                    lfRes.data[i].residential_l2_load;
                dataLoadForecastUnit.residential_mud_load =
                    lfRes.data[i].residential_mud_load;
                dataLoadForecastUnit.work_load = lfRes.data[i].work_load;
                dataLoadForecastUnit.fast_load = lfRes.data[i].fast_load;
                dataLoadForecastUnit.public_l2_load =
                    lfRes.data[i].public_l2_load;
                dataLoadForecastUnit.total_load = lfRes.data[i].total_load;
                dataLoadForecast.push(dataLoadForecastUnit);
                this.setLoadForecastResults(dataLoadForecast);
            }
        } catch (error) {
            this.handleAlertOpen(
                "Error",
                "Error occurred while loading load forecast profile."
            );
        }
    };

    setLoadForecastResults = (loadForecastData) => {
        const loadForecastResults = processResults(loadForecastData, false);
        const profileMatch = this.state.profileData.filter(
            (profile) => profile.config_name === this.state.profileName
        )[0];
        const countyChoice = profileMatch["choice"];
        const rateStructure = profileMatch["work_control"];
        this.setState({
            chartTitles: [
                `${this.state.profileName} - ${countyChoice} uncontrolled`,
                `${this.state.profileName} - ${countyChoice} ${rateStructure} controlled`,
            ],
        });
        this.setState({
            openResult: true,
            shouldRender: true,
            loadForecastResults: loadForecastResults,
        });
    };

    runCBATool = async () => {
        try {
            const configRes = await axios.get(
                `${serverUrl}/config/cost_benefit/`,
                {
                    params: {
                        lf_config: this.state.profileName,
                    },
                }
            );
            if (!configRes.data.length) {
                this.props.loadingResults(true);
                const profileMatch = this.state.profileData.filter(
                    (profile) => profile.config_name === this.state.profileName
                );
                const countyMatch = profileMatch.map(
                    (profile) => profile["choice"]
                );
                axios({
                    url: `${serverUrl}/cost_benefit_analysis_runner`,
                    method: "post",
                    data: {
                        load_profile: this.state.profileName,
                        county: countyMatch,
                    },
                }).then(
                    async (celeryRes) => {
                        const taskId = celeryRes.data.task_id;
                        let timeout;
                        await exponentialBackoff(
                            checkFlowerTaskStatus,
                            taskId,
                            timeout,
                            20,
                            75,
                            async () => {
                                this.props.loadingResults(false);
                                this.props.checkCBA(true);
                                this.downloadCbaOpen();
                                this.props.visualizeResults(
                                    await this.getCBAResult(),
                                    true
                                );
                            },
                            () => {
                                this.props.loadingResults(false);
                                this.handleAlertOpen(
                                    "Error",
                                    "Error occurred while running cost benefit analysis."
                                );
                            }
                        );
                    },
                    (error) => {
                        this.props.loadingResults(false);
                        this.handleAlertOpen(
                            "Error",
                            "Error occurred while starting cost benefit analysis runner."
                        );
                    }
                );
            } else {
                this.props.checkCBA(true);
                this.props.visualizeResults(await this.getCBAResult(), true);
            }
        } catch (error) {
            this.handleAlertOpen("Server Error", "Something went wrong");
        }
    };

    getCBAResult = async () => {
        try {
            const cbaRes = await axios.get(
                `${serverUrl}/algorithm/cost_benefit_analysis/cost_benefit`
            );
            const filteredRes = cbaRes.data.filter(
                (item) => item.config.lf_config === this.state.profileName
            );
            const dataCBA = { dataValues: [] };
            const dataCBASub = [];
            for (var i = 0; i < filteredRes.length; i++) {
                const dataCBAUnit = filteredRes[i];
                dataCBAUnit.values = filteredRes[i][this.props.controlType];
                dataCBASub.push(dataCBAUnit);
            }
            dataCBA.dataValues = dataCBASub;
            return preprocessData(dataCBA);
        } catch (error) {
            this.handleAlertOpen("Server Error", "Something went wrong");
        }
    };

    handleAlertOpen = (title, description) => {
        this.setState({
            alertTitle: title,
            alertDescription: description,
            openAlert: true,
        });
    };

    handleAlertClose = () => {
        this.setState({ openAlert: false });
    };

    downloadCbaOpen = () => {
        this.setState({ openDownloadCbaPopUp: true });
    };

    downloadCbaClose = () => {
        this.setState({ openDownloadCbaPopUp: false });
    };

    downloadCba = async () => {
        try {
            const profileMatch = this.state.profileData.filter(
                (profile) => profile.config_name === this.state.profileName
            );
            const countyMatch = profileMatch.map(
                (profile) => profile["choice"]
            );
            const params = {
                load_profile: this.state.profileName,
                county: countyMatch[0],
            };
            axios
                .get(`${serverUrl}/download_cba_zip`, {
                    params: params,
                    responseType: "blob",
                })
                .then(
                    (zipRes) => {
                        FileDownload(
                            zipRes.data,
                            `CBA_Results_${this.state.profileName}_${countyMatch[0]}.zip`
                        );
                        this.downloadCbaClose();
                    },
                    (error) => {
                        this.downloadCbaClose();
                        this.handleAlertOpen(
                            "Server Error",
                            "Something went wrong"
                        );
                    }
                );
        } catch (error) {
            this.handleAlertOpen("Server Error", "Something went wrong");
        }
    };

    handleChartsClose = () => {
        this.setState({ openResult: false });
    };

    updateCBACharts = async () => {
        this.props.checkCBA(true);
        this.props.visualizeResults(await this.getCBAResult(), true);
    };

    update = (field, event) => {
        this.setState({ [field]: event.currentTarget.value });
    };

    componentDidUpdate(prevProps) {
        if (prevProps.controlType !== this.props.controlType) {
            this.updateCBACharts();
        }
    }

    render() {
        const { classes } = this.props;
        return (
            <div>
                <Dialog
                    open={this.state.openAlert}
                    onClose={this.handleAlertClose}
                    aria-labelledby="alert-dialog-title"
                    aria-describedby="alert-dialog-description"
                >
                    <DialogTitle id="alert-dialog-title">
                        {this.state.alertTitle}
                    </DialogTitle>
                    <DialogContent>
                        <DialogContentText id="alert-dialog-description">
                            {this.state.alertDescription}
                        </DialogContentText>
                    </DialogContent>
                    <DialogActions>
                        <Button
                            onClick={this.handleAlertClose}
                            color="primary"
                            autoFocus
                        >
                            OK
                        </Button>
                    </DialogActions>
                </Dialog>
                <Dialog
                    open={this.state.openDownloadCbaPopUp}
                    onClose={this.downloadCbaClose}
                    aria-labelledby="alert-dialog-title"
                    aria-describedby="alert-dialog-description"
                >
                    <DialogTitle id="alert-dialog-title">
                        Would you like to download the Cost Benefit Analysis
                        results for {this.state.profileName}?
                    </DialogTitle>
                    <DialogContent>
                        <DialogContentText id="alert-dialog-description">
                            Warning: You will not be able to download these
                            results at a later time
                        </DialogContentText>
                    </DialogContent>
                    <DialogActions>
                        <Button
                            onClick={this.downloadCbaClose}
                            color="primary"
                            autoFocus
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={this.downloadCba}
                            variant="contained"
                            color="primary"
                            autoFocus
                        >
                            Download
                        </Button>
                    </DialogActions>
                </Dialog>
                <TextField
                    id="standard-profile"
                    select
                    className={classes.textField}
                    SelectProps={{
                        native: true,
                        MenuProps: {
                            className: classes.menu,
                        },
                    }}
                    helperText="Please select a profile"
                    margin="normal"
                    onChange={(e) => this.update("profileName", e)}
                >
                    {this.state.profileNames.map((option) => (
                        <option key={option.name} value={option.name}>
                            {option.name}
                        </option>
                    ))}
                </TextField>
                <Button
                    variant="contained"
                    className={classes.button}
                    onClick={this.getLoadForecastData}
                >
                    Review
                </Button>
                <p />
                <Button
                    variant="contained"
                    color="primary"
                    className={classes.button}
                    onClick={this.runCBATool}
                >
                    Run
                </Button>

                {!this.state.shouldRender ? (
                    <></>
                ) : (
                    <Dialog
                        classes={{
                            paper: classes.dialog,
                        }}
                        open={this.state.openResult}
                        onClose={this.handleChartsClose}
                        aria-labelledby="form-dialog-title"
                    >
                        <DialogTitle
                            onClose={this.handleChartsClose}
                            id="form-dialog-title"
                        >
                            Load Forecast Profile
                        </DialogTitle>
                        <DialogContent>
                            <ResultCharts
                                results={this.state.loadForecastResults}
                                algId={2}
                                isCBA={false}
                                graphWidth={400}
                                chartTitles={this.state.chartTitles}
                            />
                        </DialogContent>
                        <DialogActions>
                            <Button
                                onClick={this.handleChartsClose}
                                color="primary"
                            >
                                Cancel
                            </Button>
                        </DialogActions>
                    </Dialog>
                )}
            </div>
        );
    }
}

export default withStyles(styles, { withTheme: true })(AlgInputsCBA);
