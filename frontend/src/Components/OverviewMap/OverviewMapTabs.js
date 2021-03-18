import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    input: {
        display: "none",
    },
}));

function OverviewMapTabs(props) {
    const classes = useStyles();

    return (
        <>
            <Button
                className={classes.button}
                onClick={props.updateMap("totalEnergy")}
            >
                Total Energy
            </Button>
        </>
    );
}

export default OverviewMapTabs;
