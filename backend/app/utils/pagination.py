def paginate_query(query, page, per_page):
    page = max(int(page) if page and int(page) > 0 else 1, 1)
    per_page = max(min(int(per_page) if per_page and int(per_page) > 0 else 20, 100), 1)
    total = query.count()
    items = query.limit(per_page).offset((page-1)*per_page).all()
    return {
        'items': items,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }
