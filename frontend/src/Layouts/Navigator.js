import React from "react";
import PropTypes from "prop-types";
import clsx from "clsx";
import { withStyles } from "@material-ui/core/styles";
import Divider from "@material-ui/core/Divider";
import Drawer from "@material-ui/core/Drawer";
import List from "@material-ui/core/List";
import { NavLink } from "react-router-dom";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import HomeIcon from "@material-ui/icons/Home";
import PeopleIcon from "@material-ui/icons/People";
import DnsRoundedIcon from "@material-ui/icons/DnsRounded";
import PermMediaOutlinedIcon from "@material-ui/icons/PhotoSizeSelectActual";
import PublicIcon from "@material-ui/icons/Public";
import SettingsIcon from "@material-ui/icons/Settings";

const categories = [
    {
        id: "Algorithms",
        children: [
            {
                id: "alg-loadcontrol",
                name: "Load Control",
                icon: <DnsRoundedIcon />,
            },
            {
                id: "alg-loadforecast",
                name: "Load Forecast",
                icon: <PermMediaOutlinedIcon />,
            },
            {
                id: "alg-cba",
                name: "Cost Benefit Analysis",
                icon: <PublicIcon />,
            },
        ],
    },
];

const styles = (theme) => ({
    card: {
        maxWidth: 345,
        paddingTop: 10,
    },
    media: {
        height: 140,
    },
    categoryHeader: {
        paddingTop: theme.spacing(2),
        paddingBottom: theme.spacing(2),
    },
    categoryHeaderPrimary: {
        color: theme.palette.common.white,
    },
    item: {
        paddingTop: 1,
        paddingBottom: 1,
        color: "rgba(255, 255, 255, 0.7)",
        "&:hover": {
            backgroundColor: "rgba(255, 255, 255, 0.08)",
        },
    },
    itemCategory: {
        backgroundColor: "#232f3e",
        boxShadow: "0 -1px 0 #404854 inset",
        paddingTop: theme.spacing(2),
        paddingBottom: theme.spacing(2),
        fontSize: 20,
    },
    firebase: {
        fontSize: 30,
        color: theme.palette.common.white,
    },
    active: {
        color: "#4fc3f7",
        backgroundColor: "rgba(255, 255, 255, 0.08)",
    },
    itemPrimary: {
        fontSize: "inherit",
    },
    itemIcon: {
        minWidth: "auto",
        marginRight: theme.spacing(2),
    },
    divider: {
        marginTop: theme.spacing(2),
    },
});

function Navigator(props) {
    const { classes, ...other } = props;

    return (
        <Drawer variant="permanent" {...other}>
            <List disablePadding>
                <ListItem
                    className={clsx(
                        classes.firebase,
                        classes.item,
                        classes.itemCategory
                    )}
                >
                    SLAC
                </ListItem>

                <ListItem
                    className={clsx(classes.item, classes.itemCategory)}
                    button
                    component={NavLink}
                    exact
                    to={"/"}
                    activeClassName={classes.active}
                >
                    <ListItemIcon className={classes.itemIcon}>
                        <HomeIcon />
                    </ListItemIcon>
                    <ListItemText
                        classes={{
                            primary: classes.itemPrimary,
                        }}
                    >
                        Overview
                    </ListItemText>
                </ListItem>

                {categories.map(({ id, children }) => (
                    <React.Fragment key={id}>
                        <ListItem className={classes.categoryHeader}>
                            <ListItemText
                                classes={{
                                    primary: classes.categoryHeaderPrimary,
                                }}
                            >
                                <ListItemIcon className={classes.itemIcon}>
                                    <SettingsIcon />
                                </ListItemIcon>
                                {id}
                            </ListItemText>
                        </ListItem>
                        {children.map(
                            ({
                                id: childId,
                                name: childName,
                                icon,
                                active,
                            }) => (
                                <ListItem
                                    key={childId}
                                    button
                                    className={clsx(classes.item)}
                                    component={NavLink}
                                    exact
                                    to={"/" + childId}
                                    activeClassName={classes.active}
                                >
                                    <ListItemIcon className={classes.itemIcon}>
                                        {icon}
                                    </ListItemIcon>
                                    <ListItemText
                                        classes={{
                                            primary: classes.itemPrimary,
                                        }}
                                    >
                                        {childName}
                                    </ListItemText>
                                </ListItem>
                            )
                        )}

                        <Divider className={classes.divider} />
                    </React.Fragment>
                ))}

                <ListItem
                    className={clsx(classes.item, classes.itemCategory)}
                    button
                    component={NavLink}
                    exact
                    to={"/About"}
                    activeClassName={classes.active}
                >
                    <ListItemIcon className={classes.itemIcon}>
                        <PeopleIcon />
                    </ListItemIcon>
                    <ListItemText
                        classes={{
                            primary: classes.itemPrimary,
                        }}
                    >
                        About
                    </ListItemText>
                </ListItem>
            </List>
        </Drawer>
    );
}

Navigator.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(Navigator);
