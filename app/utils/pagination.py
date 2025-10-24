def paginate(query, request):
    """
    Simple pagination helper
    """
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total_items': pagination.total
    }