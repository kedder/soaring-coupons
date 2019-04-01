import $ from 'jquery'
import Time from 'react-time';
import React from "react";
import ReactDOM from "react-dom";

import {Table} from 'react-bootstrap';
import {Form} from 'react-bootstrap';

const API_URL = '/api/1/'

export class CouponListUI extends React.Component {
    constructor(props) {
        super(props);
        let now = new Date();
        this.state = {
            data: {
                coupons: []
            },
            filter: {
                year: now.getFullYear()
            }
        }
    }

    componentDidMount() {
        this.fetchData()
    }

    fetchData() {
        $.ajax({
            url: API_URL + "coupons",
            data: this.state.filter,
            method: 'GET',
            dataType: 'json',
        }).done((resp) => {
            this.setState({data: resp})
        })
    }

    refresh() {
        this.setState({filter: this.state.filter})
        this.fetchData()
    }
    renderFilterForm() {
        let filter = this.state.filter

        var thisYear = new Date().getFullYear();

        var years = [];
        for (var year = thisYear; year >= 2018; year--) {
            years.push(<option value={year} key={year}>{year}</option>);
        }

        return (
            <div>
            <form className="form-inline">
                <Form.Control as='select'
                    label="Metai&nbsp;"
                    value={this.state.filter.year}
                    onChange={(evt) => {filter.year = evt.target.value; this.refresh()}}>
                    {years}
                </Form.Control>
            </form>
            </div>
        )
    }

    renderCouponRow(coupon, n) {
        function formatCouponType(me, ctype) {
            return me.state.data.refs.coupon_types[ctype];
        }

        let urlpat = decodeURIComponent(this.state.data.refs.coupon_url_pattern);
        function formatCouponUrl(me, coupon_id) {
            return urlpat.replace('@@@', coupon_id)
        }

        return (
            <tr key={coupon.__key}>
                <td><a href={ formatCouponUrl(this, coupon.__name) }>{ coupon.__name }</a></td>
                <td><a href="mailto:{ coupon.order.payer_email }">{coupon.order.payer_email}</a></td>
                <td>{formatCouponType(this, coupon.order.coupon_type)}</td>
                <td><Time value={coupon.order.payment_time} format="YYYY-MM-DD" /></td>
                <td>{coupon.expires}</td>
                <td>{coupon.order.paid_amount} { coupon.order.paid_currency}</td>
                <td>{coupon.order.notes}</td>
                <td>{coupon.order.test}</td>
            </tr>
        )
    }

    render() {
        return (
            <div>
            <h1>Galiojantys kvietimai</h1>
            <div className="pull-right">
                {this.renderFilterForm()}
            </div>
            <p>Galiojančių kvietimų: {this.state.data.count}</p>
            <Table bordered hover >
                <thead>
                  <tr>
                    <th>Nr</th>
                    <th>Email</th>
                    <th>Tipas</th>
                    <th>Pirkimo data</th>
                    <th>Galioja iki</th>
                    <th>Sumokėta</th>
                    <th>Pastabos</th>
                    <th>Testinis?</th>
                  </tr>
                </thead>
                <tbody>
                    {this.state.data.coupons.map((coupon) => {return this.renderCouponRow(coupon)})}
                </tbody>
            </Table>

            </div>
        )
    }
}

export function renderCouponList(elem) {
    // test
    ReactDOM.render(
      <CouponListUI name="World"/>,
      elem
    );
}
