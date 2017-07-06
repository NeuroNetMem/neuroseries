ts_max = 10000000000;

t1 = [0, ts_max*0.2, 0];
t2 = [ts_max, ts_max, ts_max*0.8];


for i = 1:3
    a = int64(linspace(t1(i), t2(i), 100000)');
    d_a = randn(size(a));
    ts_a = tsd(a, d_a);
    
    b = int64(sort(rand(1000, 1) * ts_max));
    ts_b = ts(b);
    
    r_closest = Restrict(ts_a, ts_b, 'align', 'closest');
    r_next = Restrict(ts_a, ts_b, 'align', 'next');
    r_prev = Restrict(ts_a, ts_b, 'align', 'prev');
    
    
    t_closest = Range(r_closest, 'ts');
    t_next = Range(r_next, 'ts');
    t_prev = Range(r_prev, 'ts');
    d_closest = Data(r_closest);
    d_next = Data(r_next);
    d_prev = Data(r_prev);
    t_a = a;
    t_b = b;
    
    save(['/Users/fpbatta/src/batlab/neuroseries/resources/test_data/restrict_ts_data_', mat2str(i)], 't_*', 'd_*');
end
