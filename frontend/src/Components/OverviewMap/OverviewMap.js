import React from "react";
import VectorMap from "@south-paw/react-vector-maps";
import caMapData from "@south-paw/react-vector-maps/maps/json/usa-ca.json";
import svgPanZoom from "svg-pan-zoom";
import Select from "@material-ui/core/Select";
import InputLabel from "@material-ui/core/InputLabel";
import MenuItem from "@material-ui/core/MenuItem";
import FormControl from "@material-ui/core/FormControl";
import { makeStyles } from "@material-ui/core/styles";
import { rgba } from "polished";

import {
    Tooltip,
    ParamTabs,
    LegendWrapper,
    getStyledMapWrapperByCountyColors,
    addCountyColorByAttr,
    getExtremeValuesOfAttr,
    getBasicColor,
    getColorPercentageEsp,
} from "./OverviewMapStyled";
import OverviewMapLegend from "./OverviewMapLegend";
import { countyRes } from "../Api/CountyData";

const useStyles = makeStyles((theme) => ({
    formControl: {
        margin: theme.spacing(1),
        marginLeft: theme.spacing(1.5),
        minWidth: 200,
    },
    selectEmpty: {
        marginTop: theme.spacing(2),
    },
}));

const allOverviewParams = {
    total_energy: {
        id: "total-energy",
        text: "Total Energy",
        unit: "kWh",
    },
    total_session: {
        id: "total-session-num",
        text: "Total # of Session",
        unit: "cnts",
    },
    peak_energy: {
        id: "peak-energy",
        text: "Peak Energy",
        unit: "kWh",
    },
};

const ParamSelect = (props) => {
    const classes = useStyles();
    return (
        <>
            <FormControl className={classes.formControl}>
                <InputLabel id="overview-param-select-label">
                    Overview Parameter
                </InputLabel>
                <Select
                    labelId="overview-param-select-label"
                    id="overview-param-select"
                    value={props.overviewAttr}
                    onChange={(event) =>
                        props.changeOverviewAttr(event.target.value)
                    }
                >
                    {Object.keys(props.allOverviewParams).map((param) => (
                        <MenuItem
                            key={props.allOverviewParams[param].id}
                            value={param}
                        >
                            {props.allOverviewParams[param].text}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
        </>
    );
};

const counties = {};

class OverviewMap extends React.PureComponent {
    constructor(props) {
        super(props);

        this.state = {
            chosenParam: "total_energy",
            minValue: null,
            maxValue: null,
            current: {
                countyName: null,
                total_energy: null,
                total_session: null,
                peak_energy: null,
            },
            isTooltipVisible: false,
            tooltipY: 0,
            tooltipX: 0,
            gotPan: false,
            styledMap: null,
        };

        addCountyColorByAttr(counties, this.props.overviewParam);
        this.styledMap = getStyledMapWrapperByCountyColors(counties);
        this.Viewer = null;
        this.updateMap = this.updateMap.bind(this);
    }

    changeOverviewAttr(newAttr) {
        this.setState({
            chosenParam: newAttr,
        });
        this.updateMap(newAttr);
    }

    updateMap(newAttr) {
        const extremeValues = getExtremeValuesOfAttr(counties, newAttr);
        addCountyColorByAttr(counties, newAttr);
        this.setState({
            minValue: parseFloat(extremeValues.minValue.toPrecision(2)),
            maxValue: parseFloat(extremeValues.maxValue.toPrecision(2)),
            styledMap: getStyledMapWrapperByCountyColors(counties),
        });
    }

    componentDidMount = () => {
        countyRes.then((res) => {
            const countyData = res.data;
            countyData.forEach((data) => {
                counties[data.name] = {
                    total_energy: data.total_energy,
                    total_session: data.total_session,
                    peak_energy: data.peak_energy,
                };
            });
            this.updateMap("total_energy");
            svgPanZoom("#usa-ca");
        });
    };

    componentDidUpdate() {
        // const panZoomMap = svgPanZoom("#usa-ca");
    }

    render() {
        // if (!counties) {
        //     return <></>;
        // }

        const { current, isTooltipVisible, tooltipX, tooltipY } = this.state;
        const layerProps = {
            onMouseOver: this.onMouseOver,
            onMouseMove: this.onMouseMove,
            onMouseOut: this.onMouseOut,
        };

        const tooltipStyle = {
            display: isTooltipVisible ? "block" : "none",
            top: tooltipY,
            left: tooltipX,
            width: "15rem",
        };

        if (this.state.styledMap) {
            return (
                <this.state.styledMap>
                    <ParamTabs>
                        <h2>Overview Map of California</h2>
                        {
                            <ParamSelect
                                allOverviewParams={allOverviewParams}
                                changeOverviewAttr={(newAttr) =>
                                    this.changeOverviewAttr(newAttr)
                                }
                                overviewAttr={this.state.chosenParam}
                            />
                        }
                    </ParamTabs>
                    <LegendWrapper>
                        <OverviewMapLegend
                            startValue={this.state.minValue}
                            midValue={parseFloat(
                                (
                                    (this.state.maxValue +
                                        this.state.minValue) /
                                    2
                                ).toPrecision(2)
                            )}
                            endValue={this.state.maxValue}
                            unit={
                                allOverviewParams[this.state.chosenParam].unit
                            }
                            startColor={rgba(
                                ...getBasicColor(),
                                getColorPercentageEsp() /
                                    (1 + getColorPercentageEsp())
                            )}
                            endColor={rgba(...getBasicColor(), 1)}
                        />
                    </LegendWrapper>
                    <VectorMap
                        id={"overview-map"}
                        {...caMapData}
                        layerProps={layerProps}
                    />
                    <Tooltip style={tooltipStyle}>
                        <b>County:</b> {current.countyName}
                        <br />
                        <b>
                            {allOverviewParams[this.state.chosenParam].text}:
                        </b>{" "}
                        {parseFloat(current[this.state.chosenParam] / 1000)}{" "}
                        {allOverviewParams[this.state.chosenParam].unit}
                    </Tooltip>
                </this.state.styledMap>
            );
        } else {
            return <></>;
        }
    }

    onMouseOver = (e) => {
        if (!counties[e.target.attributes.name.value]) {
            return;
        }
        let newState = {
            current: {
                countyName: e.target.attributes.name.value,
                [this.state.chosenParam]: (
                    counties[e.target.attributes.name.value][
                        this.state.chosenParam
                    ] * 1000
                ).toFixed(1),
            },
        };
        this.setState(newState);
    };

    onMouseMove = (e) => {
        this.setState({
            isTooltipVisible: true,
            tooltipY: e.pageY + 10,
            tooltipX: e.pageX + 10,
        });
    };

    onMouseOut = (e) => {
        this.setState({
            isTooltipVisible: false,
        });
    };
}

export default OverviewMap;
