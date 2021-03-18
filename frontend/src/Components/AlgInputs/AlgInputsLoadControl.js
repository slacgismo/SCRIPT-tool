import React, { Component } from "react";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";
import { withStyles } from "@material-ui/core/styles";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogContentText from "@material-ui/core/DialogContentText";
import { serverUrl } from "../Api/Server";
import axios from "axios";

const styles = (theme) => ({
    container: {
        display: "flex",
        flexWrap: "wrap",
    },
    textField: {
        marginLeft: theme.spacing(1),
        marginRight: theme.spacing(1),
        width: 200,
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

class AlgInputsLoadControl extends Component {
    constructor(props) {
        super(props);
        this.state = {
            counties: [
                "All Counties",
                "Alameda",
                "Contra Costa",
                "Marin",
                "Orange",
                "Sacramento",
                "San Francisco",
                "San Mateo",
                "Santa Clara",
                "Solano",
            ],
            result: null,
            county: "Santa Clara",
            rateStructures: [
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
            rateStructure: "PGEe19",
            openAlert: false,
            alertTitle: "",
            alertDescription: "",
            chartTitles: [],
        };
    }

    update = (field, event) => {
        this.setState({ [field]: event.currentTarget.value });
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

    runAlgorithm = async () => {
        const postData = {
            county: this.state.county,
            rateStructure: this.state.rateStructure,
        };
        const postUrl = `${serverUrl}/load_control_runner`;

        axios({
            method: "post",
            url: postUrl,
            data: postData,
        }).then(
            (response) => {
                const sca_data = [JSON.parse(response.data)];
                this.props.setChartTitles([
                    `${this.state.county} - ${this.state.rateStructure}`,
                ]);
                this.props.checkCBA(false);
                this.props.visualizeResults(sca_data, false);
            },
            (error) => {
                this.handleAlertOpen("Server Error", "Something went wrong");
            }
        );
    };

    render() {
        const { classes } = this.props;
        return !this.state.counties ? (
            <></>
        ) : (
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
                <TextField
                    id="standard-county"
                    select
                    className={classes.textField}
                    SelectProps={{
                        native: true,
                        MenuProps: {
                            className: classes.menu,
                        },
                    }}
                    helperText="Please select a county"
                    margin="normal"
                    value={this.state.county}
                    onChange={(e) => this.update("county", e)}
                >
                    {this.state.counties.map((option) => (
                        <option key={option} value={option}>
                            {option}
                        </option>
                    ))}
                </TextField>
                <TextField
                    id="rateStructure"
                    select
                    value={this.state.rateStructure}
                    className={classes.textField}
                    helperText="Rate Structure"
                    SelectProps={{
                        native: true,
                        MenuProps: {
                            className: classes.menu,
                        },
                    }}
                    margin="normal"
                    onChange={(e) => this.update("rateStructure", e)}
                >
                    {this.state.rateStructures.map((option) => (
                        <option key={option} value={option}>
                            {option}
                        </option>
                    ))}
                </TextField>
                <br />
                <Button
                    variant="contained"
                    color="primary"
                    className={classes.button}
                    onClick={() => this.runAlgorithm()}
                >
                    Run
                </Button>
            </>
        );
    }
}

export default withStyles(styles, { withTheme: true })(AlgInputsLoadControl);
