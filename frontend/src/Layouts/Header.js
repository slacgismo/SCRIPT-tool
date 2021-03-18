import React from "react";
import PropTypes from "prop-types";
import AppBar from "@material-ui/core/AppBar";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import { withStyles } from "@material-ui/core/styles";
import Paper from "@material-ui/core/Paper";

const lightColor = "rgba(255, 255, 255, 0.7)";

const styles = (theme) => ({
    secondaryBar: {
        zIndex: 0,
    },
    menuButton: {
        marginLeft: -theme.spacing(1),
    },
    iconButtonAvatar: {
        padding: 4,
    },
    link: {
        textDecoration: "none",
        color: lightColor,
        "&:hover": {
            color: theme.palette.common.white,
        },
    },
    button: {
        borderColor: lightColor,
    },
});

function Header(props) {
    return (
        <React.Fragment>
            <Paper>
                <AppBar
                    position="sticky"
                    elevation={3}
                    color="primary"
                    style={{ padding: "2rem 1rem 0.5rem 1rem" }}
                >
                    <Toolbar>
                        <Typography variant="h5">
                            Smart Charging Infrastructure Planning Tool
                        </Typography>
                    </Toolbar>
                </AppBar>
            </Paper>
        </React.Fragment>
    );
}

Header.propTypes = {
    classes: PropTypes.object.isRequired,
    onDrawerToggle: PropTypes.func.isRequired,
};

export default withStyles(styles)(Header);
