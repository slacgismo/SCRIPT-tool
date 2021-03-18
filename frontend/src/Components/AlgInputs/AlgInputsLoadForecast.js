import React, { Component } from "react";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import axios from "axios";
import { loadForecastPromise, fieldsLoadForecast } from "../Api/AlgorithmData";
import { countyRes } from "../Api/CountyData";
import { loadForecastDefaultParams } from "../Api/AlgorithmDefaultParams";
import { serverUrl } from "../Api/Server";
import "./AlgInputs.css";
import { checkFlowerTaskStatus, exponentialBackoff } from "../Helpers/Helpers";

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
});

class AlgInputsLoadForecast extends Component {
    constructor(props) {
        super(props);
        this.state = {
            open: false,
            counties: [],
            advancedSettings: false,
            openAlert: false,
            alertTitle: "",
            alertDescription: "",
            // Alg params
            configName: loadForecastDefaultParams.configName,
            aggregationLevel: loadForecastDefaultParams.aggregationLevel,
            numEvs: loadForecastDefaultParams.numEvs,
            countyChoice: loadForecastDefaultParams.countyChoice,
            fastPercent: loadForecastDefaultParams.fastPercent,
            workPercent: loadForecastDefaultParams.workPercent,
            resPercent: loadForecastDefaultParams.resPercent,
            l1Percent: loadForecastDefaultParams.l1Percent,
            publicL2Percent: loadForecastDefaultParams.publicL2Percent,
            resDailyUse: loadForecastDefaultParams.resDailyUse,
            workDailyUse: loadForecastDefaultParams.workDailyUse,
            fastDailyUse: loadForecastDefaultParams.fastDailyUse,
            rentPercent: loadForecastDefaultParams.rentPercent,
            resL2Smooth: loadForecastDefaultParams.resL2Smooth,
            weekDay: loadForecastDefaultParams.weekDay,
            publicL2DailyUse: loadForecastDefaultParams.publicL2DailyUse,
            smallBatt: loadForecastDefaultParams.smallBatt,
            bigBatt: loadForecastDefaultParams.bigBatt,
            allBatt: loadForecastDefaultParams.allBatt,
            timerControl: loadForecastDefaultParams.timerControl,
            workControl: loadForecastDefaultParams.workControl,
            workControls: [
                "PGEcev",
                "PGEcev_demand",
                "PGEcev_energy",
                "PGEe19",
                "SCEtouev8",
                "SDGEmedian",
                "SDGErandom",
                "cap",
                "minpeak",
            ],
        };
    }

    componentDidMount() {
        countyRes.then((res) => {
            this.setState({
                counties: res.data,
            });
        });

        loadForecastPromise.then((res) => {
            const result = [];
            res.data.forEach((data) => {
                const filteredData = {};
                fieldsLoadForecast.forEach((field) => {
                    filteredData[field] = data[field];
                });
                result.push(filteredData);
            });
            this.setState({
                result: result,
            });
        });
    }

    handleClose = () => {
        this.setState({ open: false });
    };

    update = (field, event) => {
        this.setState({ [field]: event.currentTarget.value });
    };

    updateChartTitles = () => {
        if (this.state.aggregationLevel == "county") {
            this.props.setChartTitles([
                `${this.state.configName} - ${this.state.countyChoice} uncontrolled`,
                `${this.state.configName} - ${this.state.countyChoice} ${this.state.workControl} controlled`,
            ]);
        } else {
            this.props.setChartTitles([
                `${this.state.configName} - state uncontrolled`,
                `${this.state.configName} - state ${this.state.workControl} controlled`,
            ]);
        }
    };

    getResult = async () => {
        // receives 2 lists (uncontrolled, controlled) when form is saved
        const res = await axios.get(
            `${serverUrl}/algorithm/load_forecast?config=${this.state.configName}`
        );
        this.updateChartTitles();
        const dataLoadForecast = [];
        for (var i = 0; i < res.data.length; i++) {
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
                res.data[i].residential_l1_load;
            dataLoadForecastUnit.residential_l2_load =
                res.data[i].residential_l2_load;
            dataLoadForecastUnit.residential_mud_load =
                res.data[i].residential_mud_load;
            dataLoadForecastUnit.work_load = res.data[i].work_load;
            dataLoadForecastUnit.fast_load = res.data[i].fast_load;
            dataLoadForecastUnit.public_l2_load = res.data[i].public_l2_load;
            dataLoadForecastUnit.total_load = res.data[i].total_load;
            dataLoadForecast.push(dataLoadForecastUnit);
        }
        return dataLoadForecast;
    };

    saveResults = async () => {
        // check if current load forecast profile already exists before saving
        const config_res = await axios.get(
            `${serverUrl}/config/load_forecast?config_name=${this.state.configName}`
        );
        // if the CBA input relationship doesn't exist, insert new CBA input table rows to db
        if (config_res.data.length === 0) {
            // change var name
            const postData = {
                configName: this.state.configName,
                aggregationLevel: this.state.aggregationLevel,
                numEvs: parseInt(this.state.numEvs),
                county: this.state.countyChoice,
                fastPercent: parseFloat(this.state.fastPercent),
                workPercent: parseFloat(this.state.workPercent),
                resPercent: parseFloat(this.state.resPercent),
                l1Percent: parseFloat(this.state.l1Percent),
                publicL2Percent: parseFloat(this.state.publicL2Percent),
                resDailyUse: parseFloat(this.state.resDailyUse),
                workDailyUse: parseFloat(this.state.workDailyUse),
                fastDailyUse: parseFloat(this.state.fastDailyUse),
                rentPercent: parseFloat(this.state.rentPercent),
                resL2Smooth: this.state.resL2Smooth,
                weekDay: this.state.weekDay,
                publicL2DailyUse: parseFloat(this.state.publicL2DailyUse),
                smallBatt: parseFloat(this.state.smallBatt),
                bigBatt: parseFloat(this.state.bigBatt),
                allBatt: parseFloat(this.state.allBatt),
                timerControl: this.state.timerControl,
                workControl: this.state.workControl,
            };

            this.setState({ open: false });
            this.props.loadingResults(true);
            const postUrl = `${serverUrl}/load_forecast_runner`;

            axios({
                method: "post",
                url: postUrl,
                data: postData,
            }).then(
                async (lf_res) => {
                    const task_id = lf_res.data.task_id;
                    let timeout;
                    await exponentialBackoff(
                        checkFlowerTaskStatus,
                        task_id,
                        timeout,
                        20,
                        75,
                        async () => {
                            this.props.loadingResults(false);
                            this.props.checkCBA(false);
                            this.props.visualizeResults(
                                await this.getResult(),
                                false
                            );
                        },
                        () => {
                            this.props.loadingResults(false);
                            this.handleAlertOpen(
                                "Error",
                                "Error occurred while running load forecast algorithm."
                            );
                        }
                    );
                },
                (error) => {
                    this.props.loadingResults(false);
                    this.handleAlertOpen(
                        "Server Error",
                        "Something went wrong"
                    );
                }
            );
        } else {
            this.handleAlertOpen("Input Error", "Profile name already exists");
        }
    };

    runAlgorithm = () => {
        // check if values add up to 1 for residential and battery capacity
        let batteryMix =
            parseFloat(this.state.smallBatt) +
            parseFloat(this.state.bigBatt) +
            parseFloat(this.state.allBatt);
        let residential =
            parseFloat(this.state.l1Percent) +
            parseFloat(this.state.resPercent) +
            parseFloat(this.state.rentPercent);
        batteryMix = batteryMix.toFixed(1);
        residential = residential.toFixed(1);
        if (residential === "1.0" && batteryMix === "1.0") {
            this.setState({ open: true });
        } else {
            this.handleAlertOpen(
                "Input Error",
                "Battery Capacity and Residential fields must add up to 1"
            );
        }
    };

    advancedSettings = (e) => {
        e.preventDefault();
        this.setState({ advancedSettings: !this.state.advancedSettings });
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

    render() {
        const { classes } = this.props;
        const { advancedSettings } = this.state;
        const countiesTextField = (
            <TextField
                id="standard-county"
                select
                className={classes.textField}
                label="Please select a county"
                SelectProps={{
                    native: true,
                    MenuProps: {
                        className: classes.menu,
                    },
                }}
                margin="normal"
                value={this.state.countyChoice}
                onChange={(e) => this.update("countyChoice", e)}
            >
                {this.state.counties.map((option) => (
                    <option key={option.name} value={option.name}>
                        {option.name}
                    </option>
                ))}
            </TextField>
        );

        const countyNames =
            this.state.aggregationLevel === "county" ? countiesTextField : null;

        return (
            <>
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
                <fieldset class="field_set">
                    <legend>General Settings</legend>
                    <TextField
                        id="standard-aggregationLevel"
                        select
                        className={classes.textField}
                        SelectProps={{
                            native: true,
                            MenuProps: {
                                className: classes.menu,
                            },
                        }}
                        label="Please select an aggregation level"
                        margin="normal"
                        value={this.state.aggregationLevel}
                        onChange={(e) => this.update("aggregationLevel", e)}
                    >
                        <option key="county" value="county">
                            County
                        </option>
                        <option key="state" value="state">
                            State
                        </option>
                    </TextField>

                    {countyNames}

                    <TextField
                        id="standard-numEvs"
                        label="EVs in the State"
                        value={this.state.numEvs}
                        className={classes.textField}
                        margin="normal"
                        onChange={(e) => this.update("numEvs", e)}
                    />
                    <br />
                    <br />
                    <fieldset class="field_set">
                        <legend>Battery Capacity (must add up to 1)</legend>
                        <TextField
                            id="standard-smallBatteries"
                            label="Small"
                            value={this.state.smallBatt}
                            className={classes.textField}
                            margin="normal"
                            onChange={(e) => this.update("smallBatt", e)}
                        />
                        <TextField
                            id="standard-bigBatteries"
                            label="Big"
                            value={this.state.bigBatt}
                            className={classes.textField}
                            margin="normal"
                            onChange={(e) => this.update("bigBatt", e)}
                        />
                        <TextField
                            id="standard-allBatteries"
                            label="All"
                            value={this.state.allBatt}
                            className={classes.textField}
                            margin="normal"
                            onChange={(e) => this.update("allBatt", e)}
                        />
                    </fieldset>
                </fieldset>
                <br />
                <br />
                <fieldset class="field_set">
                    <legend>Charging Types Percentage</legend>
                    <TextField
                        id="standard-fastPercent"
                        label="Fast"
                        value={this.state.fastPercent}
                        className={classes.textField}
                        margin="normal"
                        onChange={(e) => this.update("fastPercent", e)}
                    />
                    <TextField
                        id="standard-workPercent"
                        label="Workplace"
                        value={this.state.workPercent}
                        className={classes.textField}
                        margin="normal"
                        onChange={(e) => this.update("workPercent", e)}
                    />
                    <TextField
                        id="standard-publicL2Percent"
                        label="Public"
                        value={this.state.publicL2Percent}
                        className={classes.textField}
                        margin="normal"
                        onChange={(e) => this.update("publicL2Percent", e)}
                    />
                    <br />
                    <br />
                    <fieldset class="field_set">
                        <legend>Residential (must add up to 1)</legend>
                        <TextField
                            id="standard-l1Percent"
                            label="Level 1"
                            value={this.state.l1Percent}
                            className={classes.textField}
                            margin="normal"
                            onChange={(e) => this.update("l1Percent", e)}
                        />
                        <TextField
                            id="standard-resPercent"
                            label="Level 2"
                            value={this.state.resPercent}
                            className={classes.textField}
                            margin="normal"
                            onChange={(e) => this.update("resPercent", e)}
                        />
                        <TextField
                            id="standard-rentPercent"
                            label="MUD"
                            value={this.state.rentPercent}
                            className={classes.textField}
                            margin="normal"
                            onChange={(e) => this.update("rentPercent", e)}
                        />
                    </fieldset>
                </fieldset>
                <br />
                <br />
                <fieldset class="field_set">
                    <legend>Control</legend>
                    <TextField
                        id="standard-timerControl"
                        label="Residential Timer"
                        value={this.state.timerControl}
                        className={classes.textField}
                        margin="normal"
                        onChange={(e) => this.update("timerControl", e)}
                    />
                    <TextField
                        id="standard-workControl"
                        select
                        value={this.state.workControl}
                        className={classes.textField}
                        label="Workplace"
                        SelectProps={{
                            native: true,
                            MenuProps: {
                                className: classes.menu,
                            },
                        }}
                        margin="normal"
                        onChange={(e) => this.update("workControl", e)}
                    >
                        {this.state.workControls.map((option) => (
                            <option key={option} value={option}>
                                {option}
                            </option>
                        ))}
                    </TextField>
                    <TextField
                        id="standard-resL2Smooth"
                        select
                        value={this.state.resL2Smooth}
                        className={classes.textField}
                        label="Residential Smooth"
                        SelectProps={{
                            native: true,
                            MenuProps: {
                                className: classes.menu,
                            },
                        }}
                        margin="normal"
                        onChange={(e) => this.update("resL2Smooth", e)}
                    >
                        <option key="true" value="true">
                            True
                        </option>
                        <option key="false" value="false">
                            False
                        </option>
                    </TextField>
                </fieldset>
                <br />
                <br />
                <Button
                    variant="contained"
                    color="primary"
                    className={classes.button}
                    onClick={this.advancedSettings}
                >
                    Advanced Settings
                </Button>
                {advancedSettings ? (
                    <fieldset class="field_set">
                        <legend>Advanced Settings</legend>
                        <TextField
                            id="standard-weekDay"
                            select
                            value={this.state.weekDay}
                            className={classes.textField}
                            margin="normal"
                            label="Day Type"
                            SelectProps={{
                                native: true,
                                MenuProps: {
                                    className: classes.menu,
                                },
                            }}
                            onChange={(e) => this.update("weekDay", e)}
                        >
                            <option key="true" value="true">
                                Week Day
                            </option>
                            <option key="false" value="false">
                                Week End
                            </option>
                        </TextField>
                        <br />
                        <br />
                        <fieldset class="field_set">
                            <legend>Daily Usage Percentage</legend>
                            <TextField
                                id="standard-resDailyUse"
                                label="Residential"
                                value={this.state.resDailyUse}
                                className={classes.textField}
                                margin="normal"
                                onChange={(e) => this.update("resDailyUse", e)}
                            />
                            <TextField
                                id="standard-workDailyUse"
                                label="Workplace"
                                value={this.state.workDailyUse}
                                className={classes.textField}
                                margin="normal"
                                onChange={(e) => this.update("workDailyUse", e)}
                            />
                            <TextField
                                id="standard-fastDailyUse"
                                label="Fast"
                                value={this.state.fastDailyUse}
                                className={classes.textField}
                                margin="normal"
                                onChange={(e) => this.update("fastDailyUse", e)}
                            />
                            <TextField
                                id="standard-publicL2DailyUse"
                                label="Public Level 2"
                                value={this.state.publicL2DailyUse}
                                className={classes.textField}
                                margin="normal"
                                onChange={(e) =>
                                    this.update("publicL2DailyUse", e)
                                }
                            />
                        </fieldset>
                    </fieldset>
                ) : null}
                <br />
                <p />
                <Button
                    variant="contained"
                    color="primary"
                    className={classes.button}
                    onClick={this.runAlgorithm}
                >
                    Run
                </Button>
                <Dialog
                    open={this.state.open}
                    onClose={this.handleClose}
                    aria-labelledby="form-dialog-title"
                    fullWidth={true}
                    maxWidth={"lg"}
                >
                    <DialogTitle id="form-dialog-title">Save</DialogTitle>
                    <DialogContent>
                        <DialogContentText>
                            To save the results of Load Forecast for Cost
                            Benefit Analysis, please enter your profile name.
                        </DialogContentText>
                        <TextField
                            autoFocus
                            margin="dense"
                            id="profile_name"
                            label="Profile Name"
                            value={this.state.configName}
                            onChange={(e) => this.update("configName", e)}
                            fullWidth
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleClose} color="primary">
                            Cancel
                        </Button>
                        <Button onClick={this.saveResults} color="primary">
                            Save
                        </Button>
                    </DialogActions>
                </Dialog>
            </>
        );
    }
}
export default withStyles(styles, { withTheme: true })(AlgInputsLoadForecast);
