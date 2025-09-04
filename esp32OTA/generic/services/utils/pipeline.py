from datetime import datetime, date, time, timedelta

KPI_REPORT_LEAD = [
    {
        '$group': {
            '_id': {
                'assigned_to': '$assigned_to', 
                'type': '$followup_type', 
                'sub_type': '$followup_last_work'
            }, 
            'count': {
                '$sum': 1
            }
        }
    }, {
        '$sort': {
            'assigned_to': 1
        }
    }
]

KPI_REPORT_FOLLOW_UP = [
    {
        '$group': {
            '_id': {
                'created_by': '$created_by', 
                'type': '$type', 
                'sub_type': '$sub_type'
            }, 
            'ids': {
                '$push': {
                    '$toString': '$_id'
                }
            }, 
            'count': {
                '$sum': 1
            }
        }
    }
]

KPI_REPORT_FOLLOW_UP_MEETINGS = [
    {
        '$group': {
            '_id': {
                'created_by': '$created_by', 
                'next_task': '$next_task'
            }, 
            'ids': {
                '$push': {
                    '$toString': '$_id'
                }
            }, 
            'count': {
                '$sum': 1
            }
        }
    }
]

KPI_REPORT_LEAD_COUNT = [
    {
        '$group': {
            '_id': '$created_by', 
            'lead_count': {
                '$count': {}
            }
        }
    }
]

KPI_REPORT_LEADTRANSFER_COUNT = [
    {
        '$group': {
            '_id': '$assigned_to', 
            'lead_count': {
                '$count': {}
            }, 
            'transfered': {
                '$sum': {
                    '$toInt': '$transfered'
                }
            }
        }
    }
]

KPI_REPORT_CALL_RECORDS = [
    {
        '$group': {
            '_id': {
                'created_by': '$created_by', 
                'call_type': '$call_type', 
                'duration': {
                    '$gt': [
                        '$call_duration', 0
                    ]
                }
            }, 
            'LEAD_id': {
                '$push': {
                    '$toString': '$lead_id'
                }
            }, 
            'count': {
                '$sum': 1
            }, 
            'total_time': {
                '$sum': '$call_duration'
            }, 
            'q_calls': {
                '$sum': {
                    '$cond': [
                        {
                            '$gte': [
                                '$call_duration', 30
                            ]
                        }, 1, 0
                    ]
                }
            }
        }
    }, {
        '$addFields': {
            '_id.duration': {
                '$cond': [
                    '$_id.duration', 'Yes', 'No'
                ]
            }
        }
    }
]

DASHBOARD_LEAD_COUNT = [
    {
        '$group': {
            '_id': '$transfered', 
            'new': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$updated_on', '$transfered_on'
                            ]
                        }, 1, 0
                    ]
                }
            }, 
            'overdue': {
                '$sum': {
                    '$cond': [
                        {
                            '$lt': [
                                {
                                    '$dayOfMonth': '$next_deadline'
                                }, {
                                    '$dayOfMonth': datetime.now()
                                }
                            ]
                        }, 1, 0
                    ]
                }
            }, 
            'pending': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                {
                                    '$dayOfMonth': '$next_deadline'
                                }, {
                                    '$dayOfMonth': datetime.now()
                                }
                            ]
                        }, 1, 0
                    ]
                }
            }, 
            'total': {
                '$sum': 1
            }
        }
    }
]

LAST_FOLLOWUP = [
    {
        '$sort': {
            'created_on': 1
        }
    }, {
        '$group': {
            '_id': '$lead', 
            'follow_count': {
                '$sum': 1
            }, 
            'id': {
                '$last': {
                    '$toString': '$_id'
                }
            }, 
            'follow_id': {
                '$last': '$follow_id'
            }, 
            'sub_type': {
                '$last': '$sub_type'
            }, 
            'completion_date': {
                '$last': '$completion_date'
            }, 
            'comment': {
                '$last': '$comment'
            }, 
            'next_task': {
                '$last': '$next_task'
            }, 
            'deadline': {
                '$last': '$next_deadline'
            }, 
            'created_on': {
                '$last': '$created_on'
            }, 
            'project': {
                '$last': '$next_project'
            }
        }
    }, {
        '$lookup': {
            'from': 'leads', 
            'localField': '_id', 
            'foreignField': '_id', 
            'pipeline': [
                {
                    '$addFields': {
                        '_id': {
                            '$toString': '$_id'
                        }, 
                        'created_by': {
                            '$toString': '$created_by'
                        },
                        'ref_id': '$lead_id'
                    }
                }
            ], 
            'as': 'lead'
        }
    }, {
        '$lookup': {
            'from': 'user', 
            'localField': 'lead.assigned_to', 
            'foreignField': '_id', 
            'as': 'user'
        }
    }, {
        '$project': {
            'follow_count': 1, 
            'id': {
                '$toString': '$id'
            }, 
            '_id': {
                '$toString': '$_id'
            }, 
            'follow_id': 1, 
            'sub_type': 1, 
            'completion_date': 1, 
            'comment': 1, 
            'next_task': 1, 
            'deadline': 1, 
            'created_on': 1, 
            'lead.first_name': 1, 
            'lead.phone_number': 1, 
            'lead.lead_id': 1, 
            'lead.ref_id': 1, 
            'user.name': 1, 
            'project': 1
        }
    }, {
        '$addFields': {
            'user': {
                '$arrayElemAt': [
                    '$user', 0
                ]
            }, 
            'lead': {
                '$arrayElemAt': [
                    '$lead', 0
                ]
            }
        }
    }
]

FIRST_FOLLOWUP = [
    {
        '$sort': {
            'next_deadline': 1, 
            '_id': 1
        }
    }, {
        '$group': {
            '_id': '$lead', 
            'follow_count': {
                '$sum': 1
            }, 
            'id': {
                '$first': {
                    '$toString': '$_id'
                }
            }, 
            'follow_id': {
                '$first': '$follow_id'
            }, 
            'sub_type': {
                '$first': '$sub_type'
            }, 
            'completion_date': {
                '$first': '$completion_date'
            }, 
            'comment': {
                '$first': '$comment'
            }, 
            'next_task': {
                '$first': '$next_task'
            }, 
            'deadline': {
                '$first': '$next_deadline'
            }, 
            'created_on': {
                '$first': '$created_on'
            }, 
            'project': {
                '$first': '$next_project'
            }
        }
    }, {
        '$lookup': {
            'from': 'leads', 
            'localField': '_id', 
            'foreignField': '_id', 
            'pipeline': [
                {
                    '$addFields': {
                        '_id': {
                            '$toString': '$_id'
                        }, 
                        'created_by': {
                            '$toString': '$created_by'
                        }
                    }
                }
            ], 
            'as': 'lead'
        }
    }, {
        '$lookup': {
            'from': 'user', 
            'localField': 'lead.assigned_to', 
            'foreignField': '_id', 
            'as': 'user'
        }
    }, {
        '$project': {
            'follow_count': 1, 
            'id': {
                '$toString': '$id'
            }, 
            '_id': {
                '$toString': '$_id'
            }, 
            'follow_id': 1, 
            'sub_type': 1, 
            'completion_date': 1, 
            'comment': 1, 
            'next_task': 1, 
            'deadline': 1, 
            'created_on': 1, 
            'lead.first_name': 1, 
            'lead.phone_number': 1, 
            'lead.lead_id': 1, 
            'user.name': 1, 
            'project': 1
        }
    }, {
        '$addFields': {
            'user': {
                '$arrayElemAt': [
                    '$user', 0
                ]
            }, 
            'lead': {
                '$arrayElemAt': [
                    '$lead', 0
                ]
            }
        }
    }
]

ALL_LEADS = [
    {
        '$sort': {
            '_id': -1
        }
    }, {
        '$lookup': {
            'from': 'user', 
            'localField': 'assigned_to', 
            'foreignField': '_id', 
            'as': 'user'
        }
    }, {
        '$project': {
            '_id': {
                '$toString': '$_id'
            }, 
            'created_on': {
                '$toDate': '$created_on'
            }, 
            'first_name': 1, 
            'phone_number': 1, 
            'project': 1, 
            'lead_level': 1, 
            'lead_id': 1, 
            'lead_comment': 1, 
            'followup_id': 1, 
            'followup_last_work': 1, 
            'followup_count': 1, 
            'followup_last_work_date': {
                '$toDate': {
                    '$add': [
                        '$followup_last_work_date', 18000000
                    ]
                }
            }, 
            'user.name': 1, 
            'new': {
                '$cond': [
                    {
                        '$eq': [
                            '$updated_on', '$transfered_on'
                        ]
                    }, 'NEW', ''
                ]
            }
        }
    }, {
        '$addFields': {
            'user': {
                '$arrayElemAt': [
                    '$user', 0
                ]
            }, 
            'created_on': {
                '$substrBytes': [
                    '$created_on', 0, 10
                ]
            }, 
            'followup_last_work_date': {
                '$substrBytes': [
                    '$followup_last_work_date', 0, 10
                ]
            }
        }
    }
]

ALL_LEADS_DATA = [
    {
        '$sort': {
            '_id': -1
        }
    }, {
        '$lookup': {
            'from': 'follow_up', 
            'localField': '_id', 
            'foreignField': 'lead', 
            'pipeline': [
                {
                    '$sort': {
                        '_id': 1
                    }
                }, {
                    '$group': {
                        '_id': {
                            '$toString': '$lead'
                        }, 
                        'follow_count': {
                            '$sum': 1
                        }, 
                        'id': {
                            '$last': {
                                '$toString': '$_id'
                            }
                        }, 
                        'follow_id': {
                            '$last': '$follow_id'
                        }, 
                        'sub_type': {
                            '$last': '$sub_type'
                        }, 
                        'comment': {
                            '$last': '$comment'
                        }, 
                        'level': {
                            '$last': '$lead_level'
                        }, 
                        'created_on': {
                            '$last': '$created_on'
                        }, 
                        'next_task': {
                            '$last': '$next_task'
                        }, 
                        'next_deadline': {
                            '$last': '$next_deadline'
                        }, 
                        'next_project': {
                            '$last': '$next_project'
                        }, 
                        'type': {
                            '$last': '$type'
                        }
                    }
                }
            ], 
            'as': 'followup'
        }
    }, {
        '$lookup': {
            'from': 'user', 
            'localField': 'assigned_to', 
            'foreignField': '_id', 
            'as': 'user'
        }
    }, {
        '$project': {
            '_id': {
                '$toString': '$_id'
            }, 
            'created_on': {
                '$toDate': '$created_on'
            }, 
            'first_name': 1, 
            'phone_number': 1, 
            'project': 1, 
            'lead_level': 1, 
            'lead_id': 1, 
            'followup.id': 1, 
            'followup.follow_id': 1, 
            'followup.sub_type': 1, 
            'followup.type': 1, 
            'followup.next_task': 1, 
            'followup.next_deadline': 1, 
            'followup.next_project': 1, 
            'followup.comment': 1, 
            'followup.created_on': 1, 
            'followup.follow_count': 1, 
            'followup.level': 1, 
            'user.name': 1
        }
    }, {
        '$addFields': {
            'user': {
                '$arrayElemAt': [
                    '$user', 0
                ]
            }, 
            'followup': {
                '$arrayElemAt': [
                    '$followup', 0
                ]
            }, 
            'created_on': {
                '$substrBytes': [
                    '$created_on', 0, 10
                ]
            }
        }
    }
]

GET_LEADS_KPI = [
    {
        '$sort': {
            'next_deadline': -1, 
            '_id': -1
        }
    }, {
        '$group': {
            '_id': '$lead', 
            'follow_count': {
                '$sum': 1
            }, 
            'id': {
                '$last': {
                    '$toString': '$_id'
                }
            }, 
            'follow_id': {
                '$last': '$follow_id'
            }, 
            'sub_type': {
                '$last': '$sub_type'
            }, 
            'comment': {
                '$last': '$comment'
            }, 
            'created_on': {
                '$last': {'$toDate':'$created_on'}
            }
        }
    }, {
        '$lookup': {
            'from': 'leads', 
            'localField': '_id', 
            'foreignField': '_id', 
            'pipeline': [
                {
                    '$addFields': {
                        '_id': {
                            '$toString': '$_id'
                        }, 
                        'created_by': {
                            '$toString': '$created_by'
                        }
                    }
                }
            ], 
            'as': 'lead'
        }
    }, {
        '$lookup': {
            'from': 'user', 
            'localField': 'lead.assigned_to', 
            'foreignField': '_id', 
            'as': 'user'
        }
    }, {
        '$project': {
            'follow_count': 1, 
            'id': {
                '$toString': '$id'
            }, 
            '_id': {
                '$toString': '$_id'
            }, 
            'follow_id': 1, 
            'sub_type': 1, 
            'comment': 1, 
            'created_on': 1, 
            'lead.first_name': 1, 
            'lead.phone_number': 1, 
            'lead._id': 1, 
            'lead.lead_id': 1, 
            'user.name': 1, 
            'project': 1
        }
    }, {
        '$addFields': {
            'user': {
                '$arrayElemAt': [
                    '$user', 0
                ]
            }, 
            'lead': {
                '$arrayElemAt': [
                    '$lead', 0
                ]
            }
        }
    }
]