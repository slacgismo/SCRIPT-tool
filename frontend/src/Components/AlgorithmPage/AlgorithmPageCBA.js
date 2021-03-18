import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import FormHelperText from "@material-ui/core/FormHelperText";
import FormControl from "@material-ui/core/FormControl";
import AlgorithmPage from "./AlgorithmPage";
import AlgInputsCBA from "../AlgInputs/AlgInputsCBA";

const useStyles = makeStyles((theme) => ({
    formControl: {
        margin: theme.spacing(1),
        minWidth: 120,
    },
    selectEmpty: {
        marginTop: theme.spacing(2),
    },
}));

function AlgorithmPageLoadControl(props) {
    const [controlType, setControlType] = React.useState("uncontrolled_values");

    const handleControlTypeChange = (event) => {
        setControlType(event.target.value);
    };

    const classes = useStyles();

    return (
        <AlgorithmPage
            controlType={controlType}
            compo={
                <div>
                    <FormControl className={classes.formControl}>
                        <Select
                            labelId="label-standard-category"
                            id="standard-category"
                            onChange={handleControlTypeChange}
                            value={controlType}
                            className={classes.selectEmpty}
                        >
                            <MenuItem value={"uncontrolled_values"}>
                                Uncontrolled
                            </MenuItem>
                            <MenuItem value={"controlled_values"}>
                                Controlled
                            </MenuItem>
                        </Select>
                        <FormHelperText>
                            View uncontrolled or controlled results
                        </FormHelperText>
                    </FormControl>
                </div>
            }
            title={"Cost Benefit Analysis"}
            algInputs={AlgInputsCBA}
        />
    );
}

export default AlgorithmPageLoadControl;
